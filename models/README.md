# Model Weights

This folder holds downloaded/trained model weights used by `ai-service`. It is
git-ignored (see root `.gitignore`) because weight files are large binaries that don't
belong in version control.

## Expected contents

| File | Model | Source | Used by |
|---|---|---|---|
| `yolov8s.pt` | YOLOv8s (COCO-pretrained, 80 classes) | Auto-downloaded by `ultralytics` on first run | `ai-service/app/detection/yolov8_adapter.py` |
| `best.pt` | YOLOv8s fine-tuned on gun/knife detection (2 classes) | Custom-trained — see below | `ai-service/app/weapon/yolov8_weapon_adapter.py` |
| `best_v1_original.pt` | Earlier weapon-detection fine-tune (kept for comparison) | Custom-trained, superseded by `best.pt` | Not loaded by default — reference only |

## Setting up `best.pt` (required — not in git)

`best.pt` is NOT committed to this repo (large binary, per `.gitignore`). Whoever clones
this repo needs to obtain it separately:

- Ask a project maintainer for a copy of the current `models/best.pt`, or
- Retrain it yourself: the current version was fine-tuned on the "Weapon Detect" dataset
  (5,758 images, classes: Gun, Knife, CC BY 4.0 license) from Roboflow Universe --
  https://universe.roboflow.com/train-yolov8-on-custom-dataset/weapon-detect-vwfx8 --
  starting from a stock `yolov8s.pt` checkpoint, 50 epochs, imgsz=640, trained via
  Google Colab (free T4 GPU tier). Validation results: overall mAP50 0.862 (Gun: 0.816,
  Knife: 0.908).

**Important -- label casing:** this dataset's classes are capitalized (`Gun`, `Knife`),
unlike the original fine-tune's lowercase (`gun`, `knife`). The weapon-override logic in
`ai-service/app/services/pipeline.py` compares labels case-insensitively
(`d.object.lower() in WEAPON_LABELS`) specifically to handle this -- if you retrain again
with different class name casing, this still works, but don't rely on exact-case
comparisons elsewhere in the codebase without checking this.

## Required .env values (not in git)

`ai-service/.env` is git-ignored. After copying `.env.example` to `.env`, make sure
these values are set (both were sources of real bugs found during testing):

WEAPON_ADAPTER=yolov8

Make sure this key appears only ONCE in the file -- a duplicate line lower down will
silently override it (pydantic-settings uses last-match-wins).

WEAPON_MODEL_PATH=../models/best.pt
WEAPON_CONFIDENCE_THRESHOLD=0.6

The threshold was raised from the original 0.45 after 0.45 produced a false positive
(a phone misidentified as a gun).

## Known limitation: action recognition currently disabled

`ai-service/app/services/pipeline.py` has ACTION_RECOGNITION_ENABLED = False -- real
action recognition (VideoMAE) is temporarily bypassed in favor of a placeholder
observation, isolating person/object + weapon detection for testing. Weapon detection
and its CRITICAL-alert override both work independently of this flag. Set it back to
True to re-enable VideoMAE-based action recognition.

## Known limitation: live RTSP streaming unreliable

Live RTSP ingestion (webcam -> mediamtx -> video-processing) intermittently fails with
connection timeouts that were not fully root-caused (tried: extending mediamtx's
readTimeout/writeTimeout, rewriting rtsp_source.py to use a subprocess ffmpeg pipe
instead of cv2.VideoCapture -- see git history). File-based ingestion
(--source file --path /data/your_video.mp4) works reliably and is the recommended way
to test. For fully live testing, a standalone script that reads the webcam directly via
OpenCV and POSTs frames to ai-service's /infer/frame endpoint (bypassing RTSP/mediamtx
entirely) was used successfully during development.
