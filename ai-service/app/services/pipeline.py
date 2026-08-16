from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np

from app.action_recognition.base import ActionRecognitionAdapter
from app.action_recognition.demo_heuristic import DemoHeuristicActionRecognizer
from app.captioning.base import CaptioningAdapter
from app.captioning.template_adapter import TemplateCaptioner
from app.common.frame_buffer import FrameBufferStore
from app.config import settings
from app.detection.base import ObjectDetectionAdapter
from app.detection.mock_adapter import MockDetectionAdapter
from app.schemas import ActionResult, DetectionResult
from app.threat.base import ThreatAssessmentAdapter
from app.threat.rule_based import RuleBasedThreatEngine

# One process-wide rolling buffer per camera — see app/common/frame_buffer.py.
buffer_store = FrameBufferStore()

_detection_adapter: Optional[ObjectDetectionAdapter] = None
_action_adapter: Optional[ActionRecognitionAdapter] = None
_caption_adapter: Optional[CaptioningAdapter] = None
_threat_adapter: Optional[ThreatAssessmentAdapter] = None


def get_detection_adapter() -> ObjectDetectionAdapter:
    """Lazily constructed singleton so importing this module never triggers a model
    load (useful for tests / DETECTION_ADAPTER=mock) — only the first real request does."""
    global _detection_adapter
    if _detection_adapter is None:
        if settings.detection_adapter == "yolov8":
            from app.detection.yolov8_adapter import YoloV8Adapter

            _detection_adapter = YoloV8Adapter()
        else:
            _detection_adapter = MockDetectionAdapter()
    return _detection_adapter


def get_action_adapter() -> ActionRecognitionAdapter:
    global _action_adapter
    if _action_adapter is None:
        _action_adapter = DemoHeuristicActionRecognizer()
    return _action_adapter


def get_caption_adapter() -> CaptioningAdapter:
    global _caption_adapter
    if _caption_adapter is None:
        _caption_adapter = TemplateCaptioner()
    return _caption_adapter


def get_threat_adapter() -> ThreatAssessmentAdapter:
    global _threat_adapter
    if _threat_adapter is None:
        _threat_adapter = RuleBasedThreatEngine()
    return _threat_adapter


def detect_frame(image: np.ndarray) -> List[DetectionResult]:
    return get_detection_adapter().detect(image)


def evaluate_window(camera_id: str) -> Optional[Tuple[ActionResult, datetime, datetime]]:
    """Runs Stages 2-4 (action recognition -> captioning -> threat assessment) over the
    camera's current buffered window and marks it evaluated. None if the window is empty."""
    window = buffer_store.get(camera_id)
    entries = list(window.entries)
    if not entries:
        return None

    had_previous = window.last_evaluated_at is not None
    observation = get_action_adapter().recognize(entries)
    detections = window.all_detections()
    description = get_caption_adapter().caption(detections, observation)
    threat_score, rationale = get_threat_adapter().assess(
        observation, window.last_threat_score if had_previous else None
    )

    window_start, window_end = window.window_start(), window.window_end()
    window.mark_evaluated(threat_score)

    action_result = ActionResult(
        label=observation.label,
        confidence=observation.confidence,
        description=description,
        mode=observation.mode,
        threat_score=threat_score,
        rationale=rationale,
    )
    assert window_start is not None and window_end is not None
    return action_result, window_start, window_end
