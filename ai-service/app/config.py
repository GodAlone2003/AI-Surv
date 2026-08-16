from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config, loaded from environment variables / .env. See .env.example for
    what each adapter selector means — docs/ai-pipeline.md documents which adapters are
    real models vs. clearly-labeled demo implementations."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000

    detection_adapter: str = "yolov8"  # "yolov8" (real) | "mock"
    weapon_adapter: str = "mock"  # "mock" only — no real weapon-detection model exists yet
    action_adapter: str = "demo_heuristic"
    caption_adapter: str = "template"
    threat_adapter: str = "rule_based"

    yolo_model_path: str = "../models/yolov8n.pt"
    yolo_confidence_threshold: float = 0.45

    sequence_window_seconds: int = 6

    backend_url: str = "http://localhost:4000"
    ingest_api_key: str = "INSECURE-DEV-ONLY-INGEST-KEY-change-me-before-deploying"


settings = Settings()
