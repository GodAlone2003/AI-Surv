from abc import ABC, abstractmethod
from typing import List

import numpy as np

from app.schemas import DetectionResult


class WeaponDetectionAdapter(ABC):
    """Plug-in point for a purpose-built firearm/weapon detector. No such model is
    integrated in this project — see docs/ai-pipeline.md "What requires custom training".
    A real implementation needs a labeled firearm-detection dataset and a fine-tuned (or
    from-scratch) detector; only then should this be wired into the live per-frame
    pipeline in app/services/pipeline.py."""

    mode: str

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        raise NotImplementedError
