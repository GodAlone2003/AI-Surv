import math
from datetime import datetime
from typing import Dict, List, Tuple

from app.action_recognition.base import ActionObservation, ActionRecognitionAdapter
from app.schemas import DetectionResult

# Tuning constants for the heuristic — documented here rather than magic numbers inline.
CLOSE_PROXIMITY_RATIO = 0.15  # centroid distance < 15% of frame diagonal ~= "close"
FAST_MOVEMENT_PX_PER_SEC = 80.0  # rough px/sec centroid speed threshold for "running"


class DemoHeuristicActionRecognizer(ActionRecognitionAdapter):
    """NOT a trained action-recognition model. Computes real geometry (bounding-box
    centroid proximity and movement speed) from whatever the detection stage produced,
    then maps that to a small action vocabulary with a hand-written rule set. This is
    clearly labeled mode="DEMO" everywhere it surfaces — see docs/ai-pipeline.md Stage 2
    for what a real trained model would need (dataset + GPU + training)."""

    mode = "DEMO"

    def recognize(self, window: List[Tuple[datetime, List[DetectionResult]]]) -> ActionObservation:
        if not window:
            return ActionObservation(label="no_activity", confidence=0.5, mode="DEMO", metrics={})

        person_counts = [
            len([d for d in dets if d.object == "person"]) for _, dets in window
        ]
        avg_persons = sum(person_counts) / len(person_counts)

        if avg_persons < 0.5:
            return ActionObservation(
                label="no_activity",
                confidence=0.6,
                mode="DEMO",
                metrics={"avg_person_count": avg_persons},
            )

        min_proximity_ratio, movement_speed = _proximity_and_speed(window)

        metrics = {
            "avg_person_count": avg_persons,
            "min_proximity_ratio": min_proximity_ratio if min_proximity_ratio is not None else 1.0,
            "movement_speed_px_s": movement_speed,
        }

        if avg_persons >= 2 and min_proximity_ratio is not None and min_proximity_ratio < CLOSE_PROXIMITY_RATIO:
            if movement_speed >= FAST_MOVEMENT_PX_PER_SEC:
                label, confidence = "fighting_candidate", 0.55
            else:
                label, confidence = "close_contact", 0.5
        elif avg_persons >= 2 and movement_speed >= FAST_MOVEMENT_PX_PER_SEC:
            label, confidence = "approaching", 0.5
        elif movement_speed >= FAST_MOVEMENT_PX_PER_SEC:
            label, confidence = "running", 0.5
        elif movement_speed >= FAST_MOVEMENT_PX_PER_SEC / 4:
            label, confidence = "walking", 0.55
        else:
            label, confidence = "standing", 0.55

        return ActionObservation(label=label, confidence=confidence, mode="DEMO", metrics=metrics)


def _centroid(box: List[float]) -> Tuple[float, float]:
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2


def _proximity_and_speed(
    window: List[Tuple[datetime, List[DetectionResult]]]
) -> Tuple[float | None, float]:
    """Returns (min pairwise person-centroid distance / frame diagonal, avg centroid
    movement speed in px/sec across consecutive frames — a rough, unweighted proxy, not
    per-identity tracking)."""
    min_ratio: float | None = None
    speeds: List[float] = []
    prev_centroid: Tuple[float, float] | None = None
    prev_time: datetime | None = None

    for timestamp, detections in window:
        people = [d for d in detections if d.object == "person"]
        boxes = [d.bounding_box for d in people]

        if len(boxes) >= 2:
            diag = _frame_diagonal_estimate(boxes)
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    dist = _distance(_centroid(boxes[i]), _centroid(boxes[j]))
                    ratio = dist / diag if diag else 1.0
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio

        if boxes:
            centroid = _centroid(boxes[0])
            if prev_centroid is not None and prev_time is not None:
                dt = max((timestamp - prev_time).total_seconds(), 0.001)
                speeds.append(_distance(prev_centroid, centroid) / dt)
            prev_centroid = centroid
            prev_time = timestamp

    avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
    return min_ratio, avg_speed


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _frame_diagonal_estimate(boxes: List[List[float]]) -> float:
    # No frame dimensions available here — approximate using the spread of all boxes
    # seen, which is good enough for a relative "close vs. far" ratio.
    xs = [c for box in boxes for c in (box[0], box[2])]
    ys = [c for box in boxes for c in (box[1], box[3])]
    width = max(xs) - min(xs) if xs else 1.0
    height = max(ys) - min(ys) if ys else 1.0
    return math.hypot(max(width, 1.0), max(height, 1.0)) * 3  # heuristic scale factor
