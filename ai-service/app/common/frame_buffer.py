from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, List, Optional, Tuple

from app.schemas import DetectionResult

Entry = Tuple[datetime, List[DetectionResult]]


class CameraWindow:
    """Rolling buffer of (timestamp, detections) for one camera, used by the action
    recognition / threat assessment stages — which look at a *sequence* of frames, not
    a single one. See docs/ai-pipeline.md Stage 2-4."""

    def __init__(self) -> None:
        self.entries: Deque[Entry] = deque()
        self.last_evaluated_at: Optional[datetime] = None
        self.last_threat_score: float = 0.0

    def add(self, timestamp: datetime, detections: List[DetectionResult]) -> None:
        self.entries.append((timestamp, detections))

    def prune(self, window_seconds: int) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        while self.entries and _as_utc(self.entries[0][0]) < cutoff:
            self.entries.popleft()

    def all_detections(self) -> List[DetectionResult]:
        return [d for _, dets in self.entries for d in dets]

    def window_start(self) -> Optional[datetime]:
        return self.entries[0][0] if self.entries else None

    def window_end(self) -> Optional[datetime]:
        return self.entries[-1][0] if self.entries else None

    def should_evaluate(self, window_seconds: int) -> bool:
        if not self.entries:
            return False
        if self.last_evaluated_at is None:
            return True
        elapsed = datetime.now(timezone.utc) - _as_utc(self.last_evaluated_at)
        return elapsed >= timedelta(seconds=window_seconds)

    def mark_evaluated(self, threat_score: float) -> None:
        self.last_evaluated_at = datetime.now(timezone.utc)
        self.last_threat_score = threat_score


def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class FrameBufferStore:
    """Per-camera CameraWindow registry — one process-wide instance, see app/main.py."""

    def __init__(self) -> None:
        self._windows: Dict[str, CameraWindow] = {}

    def get(self, camera_id: str) -> CameraWindow:
        if camera_id not in self._windows:
            self._windows[camera_id] = CameraWindow()
        return self._windows[camera_id]
