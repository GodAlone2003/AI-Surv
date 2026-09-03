from typing import List

import numpy as np

from app.common.logger import get_logger
from app.config import settings
from app.schemas import DetectionResult
from app.weapon.base import WeaponDetectionAdapter

logger = get_logger(__name__)


class YoloV8WeaponAdapter(WeaponDetectionAdapter):
    """Real weapon detection: YOLOv8s fine-tuned on a merged gun/knife dataset
    (see docs/ai-pipeline.md for training details and validation metrics —
    gun mAP50 0.881, knife mAP50 0.610). Detects exactly 2 classes: gun, knife."""

    mode = "REAL"

    def __init__(self) -> None:
        from ultralytics import YOLO

        logger.info(f"Loading weapon detection model from {settings.weapon_model_path} ...")
        self.model = YOLO(settings.weapon_model_path)
        self.confidence_threshold = settings.weapon_confidence_threshold
        logger.info("Weapon detection model loaded.")

    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        results = self.model.predict(image, conf=self.confidence_threshold, verbose=False)
        detections: List[DetectionResult] = []
        for result in results:
            for box in result.boxes:
                label = result.names[int(box.cls[0])]
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                detections.append(
                    DetectionResult(
                        object=label,
                        confidence=confidence,
                        bounding_box=[x1, y1, x2, y2],
                        mode="REAL",
                    )
                )
        return detections
