from abc import ABC, abstractmethod
from typing import List

from app.action_recognition.base import ActionObservation
from app.schemas import DetectionResult


class CaptioningAdapter(ABC):
    """Stage 3 interface: turns detections + a recognized action into a natural-language
    description. See docs/ai-pipeline.md Stage 3 — this project's adapter is templated,
    not a vision-language model; a real one (e.g. BLIP-2, video-LLaVA) can replace it
    behind this same interface."""

    mode: str

    @abstractmethod
    def caption(self, detections: List[DetectionResult], action: ActionObservation) -> str:
        raise NotImplementedError
