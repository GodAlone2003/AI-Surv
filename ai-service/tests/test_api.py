import base64
from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services import pipeline

client = TestClient(app)


def tiny_image_base64() -> str:
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", image)
    assert ok
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def test_health_reports_configured_adapters():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["adapters"]["detection"] == "mock"


def test_infer_frame_returns_mock_detection():
    payload = {
        "camera_id": "cam-test-1",
        "frame_timestamp": datetime.now(timezone.utc).isoformat(),
        "image_base64": tiny_image_base64(),
    }
    res = client.post("/infer/frame", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["camera_id"] == "cam-test-1"
    assert len(body["detections"]) == 1
    assert body["detections"][0]["mode"] == "DEMO"


def test_infer_frame_rejects_invalid_image():
    payload = {
        "camera_id": "cam-test-1",
        "frame_timestamp": datetime.now(timezone.utc).isoformat(),
        "image_base64": "not-valid-base64-image-data",
    }
    res = client.post("/infer/frame", json=payload)
    assert res.status_code == 400


def test_infer_sequence_after_frames_returns_action():
    camera_id = "cam-test-sequence"
    payload = {
        "camera_id": camera_id,
        "frame_timestamp": datetime.now(timezone.utc).isoformat(),
        "image_base64": tiny_image_base64(),
    }
    client.post("/infer/frame", json=payload)

    res = client.post(f"/infer/sequence?camera_id={camera_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["detections_in_window"] >= 1
    assert body["action"] is not None
    assert body["action"]["mode"] == "DEMO"


def test_infer_sequence_with_no_frames_returns_no_action():
    res = client.post("/infer/sequence?camera_id=cam-never-seen")
    assert res.status_code == 200
    body = res.json()
    assert body["action"] is None


def test_demo_scenario_endpoint_accepts_and_schedules(monkeypatch):
    # The real scenario sleeps for ~16s across its steps (see demo_scenario.py) — swap in
    # a no-op so this test verifies the endpoint contract without that real-time wait.
    async def fast_scenario(camera_id: str) -> None:
        return None

    monkeypatch.setattr("app.main.run_demo_scenario", fast_scenario)

    res = client.post("/demo/simulate-scenario?camera_id=cam-demo-1")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "started"
    assert body["mode"] == "DEMO"
