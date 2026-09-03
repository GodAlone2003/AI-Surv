import base64

import cv2
import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.common.logger import get_logger
from app.config import settings
from app.schemas import (
    FrameInferenceRequest,
    FrameInferenceResponse,
    HealthResponse,
    SequenceInferenceResponse,
)
from app.services import backend_client, pipeline
from app.services.demo_scenario import run_demo_scenario

logger = get_logger(__name__)

app = FastAPI(
    title="AI Surveillance — AI Service",
    description=(
        "Pluggable AI inference pipeline (object detection, action recognition, "
        "captioning, threat assessment). See docs/ai-pipeline.md for what's real vs. demo."
    ),
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        adapters={
            "detection": settings.detection_adapter,
            "weapon": settings.weapon_adapter,
            "action": settings.action_adapter,
            "caption": settings.caption_adapter,
            "threat": settings.threat_adapter,
        },
    )


@app.post("/infer/frame", response_model=FrameInferenceResponse)
async def infer_frame(payload: FrameInferenceRequest, background_tasks: BackgroundTasks) -> FrameInferenceResponse:
    image = _decode_image(payload.image_base64)

    detections = pipeline.detect_frame(image)
    mode = pipeline.get_detection_adapter().mode

    window = pipeline.buffer_store.get(payload.camera_id)
    window.add(payload.frame_timestamp, detections)
    window.add_frame(payload.frame_timestamp, image)
    window.prune(settings.sequence_window_seconds)

    background_tasks.add_task(
        backend_client.send_detections, payload.camera_id, mode, payload.frame_timestamp, detections
    )

    action_evaluated = False
    if window.should_evaluate(settings.sequence_window_seconds):
        result = pipeline.evaluate_window(payload.camera_id)
        if result:
            action_result, window_start, window_end = result
            background_tasks.add_task(
                backend_client.send_action, payload.camera_id, action_result, window_start, window_end
            )
            action_evaluated = True

    return FrameInferenceResponse(
        camera_id=payload.camera_id,
        detections=detections,
        mode=mode,  # type: ignore[arg-type]
        action_evaluated=action_evaluated,
    )


@app.post("/infer/sequence", response_model=SequenceInferenceResponse)
async def infer_sequence(camera_id: str, background_tasks: BackgroundTasks) -> SequenceInferenceResponse:
    """Manually triggers Stage 2-4 evaluation over whatever is currently buffered for
    this camera, instead of waiting for SEQUENCE_WINDOW_SECONDS to elapse. Useful for
    tests and for demo scripts that want tighter control over timing."""
    result = pipeline.evaluate_window(camera_id)
    detections_in_window = len(pipeline.buffer_store.get(camera_id).all_detections())

    if not result:
        return SequenceInferenceResponse(camera_id=camera_id, detections_in_window=0, action=None)

    action_result, window_start, window_end = result
    background_tasks.add_task(backend_client.send_action, camera_id, action_result, window_start, window_end)

    return SequenceInferenceResponse(
        camera_id=camera_id, detections_in_window=detections_in_window, action=action_result
    )


@app.post("/demo/simulate-scenario")
async def simulate_scenario(camera_id: str, background_tasks: BackgroundTasks) -> dict:
    """Kicks off the scripted DEMO escalation timeline (docs/demo.md) for a camera. Runs
    in the background and posts each step to the backend as it happens."""
    background_tasks.add_task(run_demo_scenario, camera_id)
    return {"status": "started", "camera_id": camera_id, "mode": "DEMO"}


def _decode_image(image_base64: str) -> np.ndarray:
    try:
        raw = base64.b64decode(image_base64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as exc:  # noqa: BLE001 — surface as a clean 400, not a 500
        raise HTTPException(status_code=400, detail=f"Invalid image data: {exc}") from exc
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image (unsupported format?)")
    return image
