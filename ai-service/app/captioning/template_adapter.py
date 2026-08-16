from collections import Counter
from typing import List

from app.action_recognition.base import ActionObservation
from app.captioning.base import CaptioningAdapter
from app.schemas import DetectionResult

_ACTION_PHRASES = {
    "no_activity": "No significant activity detected.",
    "standing": "{people} standing in view.",
    "walking": "{people} walking through the scene.",
    "running": "{people} moving quickly through the scene.",
    "approaching": "{people} approaching one another.",
    "close_contact": "{people} in close proximity to one another.",
    "fighting_candidate": "Aggressive movement and close physical contact detected between {people}.",
}


class TemplateCaptioner(CaptioningAdapter):
    """NOT a vision-language model — composes a sentence from the object counts and the
    recognized action label using fixed templates. See docs/ai-pipeline.md Stage 3."""

    mode = "DEMO"

    def caption(self, detections: List[DetectionResult], action: ActionObservation) -> str:
        counts = Counter(d.object for d in detections)
        people = counts.get("person", 0)
        people_phrase = _people_phrase(people)

        template = _ACTION_PHRASES.get(action.label, "{people} observed in the scene.")
        sentence = template.format(people=people_phrase)

        other_objects = [obj for obj in counts if obj != "person"]
        if other_objects:
            sentence += f" Also detected: {', '.join(sorted(other_objects))}."

        return sentence


def _people_phrase(count: int) -> str:
    if count == 0:
        return "No people"
    if count == 1:
        return "One person"
    if count == 2:
        return "Two people"
    return f"{count} people"
