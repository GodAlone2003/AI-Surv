import os

# Must run before any `app.*` module is imported anywhere in the test session, so
# Settings() picks these up — DETECTION_ADAPTER=mock avoids loading the real YOLO model
# (slow, and unnecessary for testing the pipeline's logic/wiring).
os.environ.setdefault("DETECTION_ADAPTER", "mock")
os.environ.setdefault("INGEST_API_KEY", "test-only-ingest-key-not-for-prod-1234567890")
os.environ.setdefault("BACKEND_URL", "http://127.0.0.1:59999")  # deliberately unreachable
