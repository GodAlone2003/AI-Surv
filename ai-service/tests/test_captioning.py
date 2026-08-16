from app.action_recognition.base import ActionObservation
from app.captioning.template_adapter import TemplateCaptioner
from app.schemas import DetectionResult


def test_caption_mentions_person_count():
    captioner = TemplateCaptioner()
    detections = [
        DetectionResult(object="person", confidence=0.9, bounding_box=[0, 0, 10, 10], mode="DEMO"),
        DetectionResult(object="person", confidence=0.9, bounding_box=[20, 20, 30, 30], mode="DEMO"),
    ]
    action = ActionObservation(label="standing", confidence=0.6, mode="DEMO", metrics={})
    caption = captioner.caption(detections, action)
    assert "Two people" in caption


def test_caption_mentions_other_objects():
    captioner = TemplateCaptioner()
    detections = [
        DetectionResult(object="person", confidence=0.9, bounding_box=[0, 0, 10, 10], mode="DEMO"),
        DetectionResult(object="car", confidence=0.9, bounding_box=[20, 20, 30, 30], mode="DEMO"),
    ]
    action = ActionObservation(label="walking", confidence=0.6, mode="DEMO", metrics={})
    caption = captioner.caption(detections, action)
    assert "car" in caption


def test_caption_handles_no_people():
    captioner = TemplateCaptioner()
    action = ActionObservation(label="no_activity", confidence=0.6, mode="DEMO", metrics={})
    caption = captioner.caption([], action)
    assert "No significant activity" in caption
