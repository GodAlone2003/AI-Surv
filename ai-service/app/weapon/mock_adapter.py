from typing import List

import numpy as np

from app.schemas import DetectionResult
from app.weapon.base import WeaponDetectionAdapter


class MockWeaponAdapter(WeaponDetectionAdapter):
    """Demo-only placeholder. Not wired into the live per-frame pipeline by default
    (app/services/pipeline.py) — real weapon detection requires a purpose-trained model
    (see docs/ai-pipeline.md), and this project does not fabricate one. Exists so the
    interface/contract is exercised (see tests/test_weapon_adapter.py) and so the demo
    scenario (app/services/demo_scenario.py) can inject a clearly-labeled synthetic
    weapon-detection event for demonstrating the alert pipeline end-to-end."""

    mode = "DEMO"

    def detect(self, image: np.ndarray) -> List[DetectionResult]:
        # Always returns no detections when called on a real frame — this project makes
        # no claim of real weapon-detection capability. See demo_scenario.py for the
        # explicit, clearly-labeled synthetic event used in Demo Mode instead.
        return []
