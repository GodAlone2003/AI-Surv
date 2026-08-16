from datetime import datetime, timedelta, timezone

from app.action_recognition.demo_heuristic import DemoHeuristicActionRecognizer
from app.schemas import DetectionResult


def person(x1: float, y1: float, x2: float, y2: float) -> DetectionResult:
    return DetectionResult(object="person", confidence=0.9, bounding_box=[x1, y1, x2, y2], mode="DEMO")


def test_empty_window_is_no_activity():
    recognizer = DemoHeuristicActionRecognizer()
    result = recognizer.recognize([])
    assert result.label == "no_activity"


def test_stationary_single_person_is_standing():
    recognizer = DemoHeuristicActionRecognizer()
    t0 = datetime.now(timezone.utc)
    window = [(t0 + timedelta(seconds=i), [person(100, 100, 150, 200)]) for i in range(4)]
    result = recognizer.recognize(window)
    assert result.label == "standing"
    assert result.mode == "DEMO"


def test_fast_moving_single_person_is_running():
    recognizer = DemoHeuristicActionRecognizer()
    t0 = datetime.now(timezone.utc)
    window = [
        (t0, [person(0, 0, 50, 100)]),
        (t0 + timedelta(seconds=1), [person(500, 0, 550, 100)]),
    ]
    result = recognizer.recognize(window)
    assert result.label == "running"


def test_two_people_close_together_is_close_contact_or_fighting():
    recognizer = DemoHeuristicActionRecognizer()
    t0 = datetime.now(timezone.utc)
    window = [
        (t0 + timedelta(seconds=i), [person(100, 100, 130, 200), person(105, 100, 135, 200)])
        for i in range(4)
    ]
    result = recognizer.recognize(window)
    assert result.label in ("close_contact", "fighting_candidate")
    assert result.metrics["min_proximity_ratio"] < 0.15
