# AI Pipeline

## Pipeline stages

```
Video → Frame extraction → Object detection → Action recognition →
  Video/scene captioning → Temporal analysis → Threat assessment → Alert generation
```

Each stage is an abstract interface in `ai-service/app/<stage>/base.py`, with one or more
concrete adapters registered in `ai-service/app/config.py`. `backend` and `frontend`
never see adapter internals — only the structured JSON contract below.

## Honesty policy (read this before trusting any result field)

Every inference result carries a `mode` field: `"real"` or `"demo"`. The frontend renders
a visible **DEMO** badge on anything with `mode: "demo"`. Nothing simulated is ever shown
as if it were a real detection.

## Stage 1 — Object Detection

- **Adapter:** `YoloV8Adapter` (Ultralytics YOLOv8n, COCO-pretrained) — **real model**,
  CPU-capable, runs today. Verified working end-to-end in this project (see the root
  README's verification notes).
- **Supported classes:** all 80 stock COCO classes, including `person`, `car`, `truck`,
  `bus`, `motorcycle`, `bicycle`, and — notably — `knife` (a dining/kitchen-context COCO
  class). The full list is in `ai-service/app/detection/yolov8_adapter.py`
  (`COCO_CLASSES`). Person/vehicle detection is the reliable, intended use here.
- **Weapon/firearm detection:** COCO has **no firearm/gun class at all**, and its `knife`
  class was annotated from dining-table photos, not threat scenarios — it is not a
  substitute for a purpose-built weapon detector and this project does not treat YOLO's
  `knife` label as a weapon alert. A separate `WeaponDetectionAdapter` interface
  (`ai-service/app/weapon/`) exists as the plug-in point for a real detector; using it for
  real requires a custom-trained model on a labeled firearm dataset (see "What requires
  custom training" below). Its current implementation, `MockWeaponAdapter`, always
  returns no detections on real frames — it exists to exercise the interface/contract,
  not to fabricate alerts. It is **not** wired into the live per-frame pipeline.
- **Output contract:**
  ```json
  { "object": "person", "confidence": 0.94, "bounding_box": [x1, y1, x2, y2], "mode": "real" }
  ```

## Stage 2 — Action Recognition

- **Interface:** `ActionRecognitionAdapter.recognize(window)` consumes a rolling
  sequence of `(timestamp, detections)` — not a single frame — buffered per-camera by
  `ai-service/app/common/frame_buffer.py` over `SEQUENCE_WINDOW_SECONDS`.
- **Current adapter:** `DemoHeuristicActionRecognizer` — computes **real geometry** from
  whatever the detection stage produced (person bounding-box centroid proximity and
  movement speed across the window) and maps it to a small action vocabulary
  (`standing`, `walking`, `running`, `approaching`, `close_contact`,
  `fighting_candidate`, `no_activity`) via a hand-written, documented rule set (see
  `ai-service/app/action_recognition/demo_heuristic.py`). The inputs can be real (when
  running on real YOLOv8 detections); the *labeling rule* is a heuristic, not a trained
  classifier — hence `mode: "DEMO"` end to end.
- **Plug-in point:** `ActionRecognitionAdapter` (ABC) — a real implementation (e.g. a
  PyTorchVideo MViT/SlowFast checkpoint) can be dropped in without touching callers.

## Stage 3 — Video Captioning

- **Interface:** `CaptioningAdapter.caption(detections, action)` returns a
  natural-language description.
- **Current adapter:** `TemplateCaptioner` — composes a sentence from detected object
  counts and the recognized action label (e.g. *"Two people approaching one another."*).
  Labeled `mode: "DEMO"` because it is templated, not a vision-language model.
- **Plug-in point:** `CaptioningAdapter` (ABC) — a real implementation (e.g. BLIP-2 or a
  video-LLaVA-style model) can replace it.

## Stage 4 — Temporal Analysis / Threat Assessment

- **This is the project's core research contribution.** `ThreatAssessmentAdapter.assess()`
  looks at the recognized action + its geometric metrics, plus the previous window's
  score (to detect a rising/sustained trend) — never a single frame — and returns a
  0.0–1.0 score with a rationale string.
- **Current implementation:** `RuleBasedThreatEngine`
  (`ai-service/app/threat/rule_based.py`) — fully transparent, hand-set weights: a base
  score per action label, +0.10 for close physical proximity, +0.05 for fast movement,
  and up to +0.15 for a rising/sustained trend across windows. Every point in the final
  score is traceable in the returned rationale string (e.g. *"base risk for
  'fighting_candidate' = 0.70 + close physical proximity (+0.10) + sustained/rising
  activity across recent windows (+0.15) = 0.95. Potential escalation to physical
  violence."*). This score is then handed to the **backend's** Threat Engine
  (`backend/src/services/threatEngine.service.ts` +
  `backend/src/config/threatConfig.ts`), which owns the score→severity thresholds and
  Alert/Incident creation — see `docs/architecture.md`.
- **Framing:** results are surfaced as **"Potential Threat / Escalation Prediction"** with
  a numeric score and a human-readable rationale — never as a claim of certainty about
  future events.
- **Plug-in point:** `ThreatAssessmentAdapter` (ABC) — a trained temporal sequence model
  can later replace the rule-based engine using the same interface.

## What requires custom training / data (not available today)

| Capability | What's needed |
|---|---|
| Real firearm/weapon detection | A labeled firearm-detection dataset (e.g. bounding boxes for handguns/rifles across varied angles/lighting) + fine-tuning a detector (YOLOv8 or similar) on it, plus a held-out validation set to report real precision/recall — none of which exists in this project yet. |
| Real action recognition (fighting/pushing/striking) | A labeled video-action dataset (e.g. a violence-detection or activity-recognition corpus), a GPU for training a temporal model, and an evaluation protocol. |
| Real video captioning | Either an API-based hosted VLM, or a locally-run open-weight video-captioning model + GPU for acceptable latency. |
| Trained temporal threat model | Historical labeled incident sequences (which don't exist without real deployment data) to move beyond the rule-based engine. |

## Endpoints (ai-service)

- `GET /health` — which adapter is active for each stage.
- `POST /infer/frame` — `{camera_id, frame_timestamp, image_base64}`. Runs Stage 1 on
  the frame, buffers it into that camera's window, forwards detections to the backend,
  and — once the window's evaluation interval has elapsed — also runs Stages 2-4 and
  forwards that result too. This is the endpoint `video-processing` calls per sampled
  frame; see `docs/architecture.md`.
- `POST /infer/sequence?camera_id=...` — manually triggers Stages 2-4 over whatever is
  currently buffered, without waiting for the time-based trigger (used by tests/demos).
- `POST /demo/simulate-scenario?camera_id=...` — plays a scripted DEMO escalation
  timeline (standing → approaching → aggressive movement → physical contact → potential
  fight) directly against the backend for a given camera, bypassing frame analysis
  entirely. Verified end-to-end in this project: it correctly produces LOW → MEDIUM →
  HIGH → CRITICAL alerts and a backend-created Incident once severity crosses HIGH. See
  `docs/demo.md` and `ai-service/app/services/demo_scenario.py`.

## Verified in this project

Unlike a spec that only describes intended behavior, the pieces above have been run:
real YOLOv8n loading and inferring on a frame (see `ai-service/README.md`), the full
video-processing → ai-service → backend chain forwarding a real (zero-detection, on
synthetic blank footage) result end-to-end, and the demo scenario producing the exact
LOW→MEDIUM→HIGH→CRITICAL escalation with a backend-created Alert + Incident.
