from typing import Optional, Tuple

from app.action_recognition.base import ActionObservation
from app.threat.base import ThreatAssessmentAdapter

# Transparent, hand-set weights — not learned from data. Documented here so the score is
# always explainable (see docs/ai-pipeline.md Stage 4). A trained temporal model could
# replace this class behind the same ThreatAssessmentAdapter interface later.
BASE_SCORE_BY_ACTION = {
    "no_activity": 0.0,
    "standing": 0.05,
    "walking": 0.08,
    "running": 0.25,
    "approaching": 0.30,
    "close_contact": 0.40,
    "fighting_candidate": 0.70,
}

CLOSE_PROXIMITY_RATIO = 0.15
PROXIMITY_BONUS = 0.10
FAST_MOVEMENT_PX_PER_SEC = 80.0
MOVEMENT_BONUS = 0.05
ESCALATION_BONUS_CAP = 0.15


class RuleBasedThreatEngine(ThreatAssessmentAdapter):
    """Weighted, fully transparent scoring — every point added to the score is
    traceable in the returned rationale string. This is "Temporal activity analysis and
    potential threat/escalation prediction": it reasons over the current window plus the
    trend from the previous window, never a single frame, and never claims certainty."""

    mode = "DEMO"  # built on demo-heuristic action recognition; see docs/ai-pipeline.md

    def assess(
        self, action: ActionObservation, previous_score: Optional[float]
    ) -> Tuple[float, str]:
        base = BASE_SCORE_BY_ACTION.get(action.label, 0.1)
        parts = [f"base risk for '{action.label}' = {base:.2f}"]
        score = base

        proximity = action.metrics.get("min_proximity_ratio")
        if proximity is not None and proximity < CLOSE_PROXIMITY_RATIO:
            score += PROXIMITY_BONUS
            parts.append(f"close physical proximity (+{PROXIMITY_BONUS:.2f})")

        speed = action.metrics.get("movement_speed_px_s", 0.0)
        if speed >= FAST_MOVEMENT_PX_PER_SEC:
            score += MOVEMENT_BONUS
            parts.append(f"fast movement (+{MOVEMENT_BONUS:.2f})")

        if previous_score is not None and previous_score > 0.25 and score >= previous_score:
            bonus = min(ESCALATION_BONUS_CAP, (score - previous_score) * 0.5 + 0.05)
            score += bonus
            parts.append(f"sustained/rising activity across recent windows (+{bonus:.2f})")

        score = max(0.0, min(1.0, score))

        rationale = f"{' + '.join(parts)} = {score:.2f}."
        if score >= 0.65:
            rationale += " Potential escalation to physical violence."
        elif score >= 0.4:
            rationale += " Elevated activity warranting attention."

        return score, rationale
