from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple

from app.schemas import DetectionResult


@dataclass
class ActionObservation:
    """Output of the action recognition stage. `metrics` carries the raw geometric
    signals (proximity, movement speed, person count) so the captioning and threat
    stages can use them without recomputing — see docs/ai-pipeline.md Stage 2."""

    label: str
    confidence: float
    mode: str  # "REAL" or "DEMO"
    metrics: Dict[str, float] = field(default_factory=dict)


class ActionRecognitionAdapter(ABC):
    """Stage 2 interface: consumes a *sequence* of (timestamp, detections) — not a
    single frame — and returns a recognized action. See docs/ai-pipeline.md Stage 2 for
    why this project's current adapter is a geometric heuristic, not a trained model,
    and what a real one would need."""

    mode: str

    @abstractmethod
    def recognize(self, window: List[Tuple[datetime, List[DetectionResult]]]) -> ActionObservation:
        raise NotImplementedError
