from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

InferenceMode = Literal["REAL", "DEMO"]


class DetectionResult(BaseModel):
    object: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: List[float] = Field(min_length=4, max_length=4)
    mode: InferenceMode


class FrameInferenceRequest(BaseModel):
    camera_id: str
    frame_timestamp: datetime
    image_base64: str
    """JPEG/PNG image, base64-encoded (no data: URI prefix)."""


class FrameInferenceResponse(BaseModel):
    camera_id: str
    detections: List[DetectionResult]
    mode: InferenceMode
    action_evaluated: bool
    """True if this frame triggered an action/threat evaluation for the camera's window."""


class ActionResult(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    description: Optional[str] = None
    mode: InferenceMode
    threat_score: float = Field(ge=0, le=1)
    rationale: Optional[str] = None


class SequenceInferenceResponse(BaseModel):
    camera_id: str
    detections_in_window: int
    action: Optional[ActionResult] = None


class HealthResponse(BaseModel):
    ok: bool
    service: str = "ai-service"
    adapters: dict
