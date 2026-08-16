from app.action_recognition.base import ActionObservation
from app.threat.rule_based import RuleBasedThreatEngine


def make_observation(label: str, **metrics: float) -> ActionObservation:
    return ActionObservation(label=label, confidence=0.6, mode="DEMO", metrics=metrics)


def test_no_activity_scores_zero():
    engine = RuleBasedThreatEngine()
    score, rationale = engine.assess(make_observation("no_activity"), previous_score=None)
    assert score == 0.0
    assert "no_activity" in rationale


def test_fighting_candidate_scores_higher_than_standing():
    engine = RuleBasedThreatEngine()
    standing_score, _ = engine.assess(make_observation("standing"), previous_score=None)
    fighting_score, _ = engine.assess(make_observation("fighting_candidate"), previous_score=None)
    assert fighting_score > standing_score


def test_close_proximity_adds_bonus():
    engine = RuleBasedThreatEngine()
    base_score, _ = engine.assess(make_observation("close_contact"), previous_score=None)
    close_score, _ = engine.assess(
        make_observation("close_contact", min_proximity_ratio=0.05), previous_score=None
    )
    assert close_score > base_score


def test_sustained_escalation_adds_bonus_and_is_capped_at_one():
    engine = RuleBasedThreatEngine()
    score, rationale = engine.assess(
        make_observation("fighting_candidate", min_proximity_ratio=0.05, movement_speed_px_s=200),
        previous_score=0.9,
    )
    assert score <= 1.0
    assert "escalation" in rationale.lower() or "rising" in rationale.lower()


def test_score_is_always_within_bounds():
    engine = RuleBasedThreatEngine()
    for label in ["no_activity", "standing", "walking", "running", "approaching", "close_contact", "fighting_candidate", "unknown_label"]:
        score, _ = engine.assess(make_observation(label, min_proximity_ratio=0.01, movement_speed_px_s=500), previous_score=0.95)
        assert 0.0 <= score <= 1.0
