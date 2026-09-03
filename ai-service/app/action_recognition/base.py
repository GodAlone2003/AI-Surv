from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.schemas import DetectionResult


@dataclass
class ActionObservation:
    """Output of the action recognition stage. metrics carries the raw geometric
    signals (proximity, movement speed, person count) so the captioning and threat
    stages can use them without recomputing."""

    label: str
    confidence: float
    mode: str
    metrics: Dict[str, float] = field(default_factory=dict)


class ActionRecognitionAdapter(ABC):
    """Stage 2 interface: consumes a sequence of (timestamp, detections), and
    optionally a sequence of raw frames for adapters that need real pixels
    (e.g. VideoMAE) rather than just bounding-box geometry."""

    mode: str

    @abstractmethod
    def recognize(
        self,
        window: List[Tuple[datetime, List[DetectionResult]]],
        frames: Optional[List[np.ndarray]] = None,
    ) -> ActionObservation:
        raise NotImplementedError
