# Model Weights

This folder holds downloaded/trained model weights used by `ai-service`. It is
git-ignored (see root `.gitignore`) because weight files are large binaries that don't
belong in version control.

## Expected contents (populated as each AI phase is built)

| File | Model | Source | Used by |
|---|---|---|---|
| `yolov8n.pt` | YOLOv8n (COCO-pretrained) | Auto-downloaded by `ultralytics` on first run, or place manually here | `ai-service/app/detection/yolov8_adapter.py` |

No custom-trained weapon-detection or action-recognition weights exist in this project —
see [`../docs/ai-pipeline.md`](../docs/ai-pipeline.md) for what training/data those would
require.
