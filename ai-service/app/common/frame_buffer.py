from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from app.schemas import DetectionResult

Entry = Tuple[datetime, List[DetectionResult]]
FrameEntry = Tuple[datetime, np.ndarray]


class CameraWindow:
    """Rolling buffer of (timestamp, detections) AND (timestamp, raw frame) for one
    camera. The detections history feeds the geometric heuristic / threat scoring; the
    raw-frame history feeds real video models (e.g. VideoMAE) that need actual pixels,
    not just bounding boxes. See docs/ai-pipeline.md Stage 2."""

    def __init__(self) -> None:
        self.entries: Deque[Entry] = deque()
        self.frames: Deque[FrameEntry] = deque()
        self.last_evaluated_at: Optional[datetime] = None
        self.last_threat_score: float = 0.0

    def add(self, timestamp: datetime, detections: List[DetectionResult]) -> None:
        self.entries.append((timestamp, detections))

    def add_frame(self, timestamp: datetime, frame: np.ndarray) -> None:
        self.frames.append((timestamp, frame))

    def prune(self, window_seconds: int) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        while self.entries and _as_utc(self.entries[0][0]) < cutoff:
            self.entries.popleft()
        while self.frames and _as_utc(self.frames[0][0]) < cutoff:
            self.frames.popleft()

    def all_detections(self) -> List[DetectionResult]:
        return [d for _, dets in self.entries for d in dets]

    def latest_detections(self) -> List[DetectionResult]:
        return self.entries[-1][1] if self.entries else []

    def get_frame_sequence(self, num_frames: int = 16) -> List[np.ndarray]:
        """Returns exactly `num_frames` frames spanning the current buffered window —
        evenly sampled if we have more than enough, padded by repeating the last frame
        if we have fewer (e.g. right after a camera first goes live). Empty list if no
        frames have been buffered yet."""
        if not self.frames:
            return []
        images = [f for _, f in self.frames]
        if len(images) >= num_frames:
            idxs = np.linspace(0, len(images) - 1, num_frames).astype(int)
            return [images[i] for i in idxs]
        return images + [images[-1]] * (num_frames - len(images))

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
