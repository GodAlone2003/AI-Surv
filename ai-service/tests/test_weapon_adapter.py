import numpy as np

from app.weapon.mock_adapter import MockWeaponAdapter


def test_mock_weapon_adapter_is_labeled_demo():
    adapter = MockWeaponAdapter()
    assert adapter.mode == "DEMO"


def test_mock_weapon_adapter_never_fabricates_a_real_detection():
    adapter = MockWeaponAdapter()
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    detections = adapter.detect(image)
    assert detections == []
