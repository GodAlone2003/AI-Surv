
import { prisma } from "../lib/prisma";
import { broadcast } from "../websocket";
import { evaluateAction } from "./threatEngine.service";
import type { IngestActionInput, IngestDetectionsInput } from "../schemas/inference.schema";

/** Marks a camera as actively seen. Flips status to ONLINE and broadcasts only on the
 * actual OFFLINE -> ONLINE transition, to avoid spamming an event on every frame. */
async function markCameraSeen(cameraId: string) {
  const camera = await prisma.camera.findUnique({ where: { id: cameraId } });
  if (!camera) return;

  const wasOffline = camera.status !== "ONLINE";
  const updated = await prisma.camera.update({
    where: { id: cameraId },
    data: { lastSeenAt: new Date(), status: "ONLINE" },
  });

  if (wasOffline) broadcast("camera.online", { cameraId, camera: updated });
}

/** Persists a batch of object-detection results from ai-service and broadcasts each. */
export async function ingestDetections(input: IngestDetectionsInput) {
  await markCameraSeen(input.cameraId);

  const created = await prisma.$transaction(
    input.detections.map((d) =>
      prisma.detection.create({
        data: {
          cameraId: input.cameraId,
          objectLabel: d.objectLabel,
          confidence: d.confidence,
          boundingBox: JSON.stringify(d.boundingBox),
          frameTimestamp: new Date(d.frameTimestamp),
          mode: input.mode,
        },
      })
    )
  );

  for (const detection of created) broadcast("detection.created", detection);
  return created;
}

/**
 * Persists a recognized action/caption result from ai-service, broadcasts it, and hands
 * it to the Threat Engine to decide whether it warrants an Alert/Incident.
 */
export async function ingestAction(input: IngestActionInput) {
  const action = await prisma.action.create({
    data: {
      cameraId: input.cameraId,
      label: input.label,
      confidence: input.confidence,
      description: input.description,
      windowStart: new Date(input.windowStart),
      windowEnd: new Date(input.windowEnd),
      mode: input.mode,
      threatScoreHint: input.threatScore,
    },
  });

  broadcast("action.detected", action);

  const result = await evaluateAction(action);
  return { action, ...result };
}
