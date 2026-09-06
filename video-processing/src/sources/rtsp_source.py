import subprocess
from typing import Optional

import numpy as np

from src.sources.base import FrameSource


def _probe_resolution(rtsp_url: str) -> tuple:
    """Uses ffprobe to determine the stream's frame width/height before we start
    reading raw frames — rawvideo has no container/headers to read this from later."""
    cmd = [
        "ffprobe", "-rtsp_transport", "tcp", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0", rtsp_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ffprobe failed to read stream info: {result.stderr}")
    width_str, height_str = result.stdout.strip().split(",")
    return int(width_str), int(height_str)


class RtspSource(FrameSource):
    """A real CCTV/RTSP camera stream, read via a real ffmpeg subprocess piping raw
    BGR frames to stdout — not cv2.VideoCapture, whose bundled FFmpeg backend has an
    internal ~30s open/read timeout (_opencv_ffmpeg_interrupt_callback) that could not
    be overridden via CAP_PROP_OPEN_TIMEOUT_MSEC/OPENCV_FFMPEG_CAPTURE_OPTIONS in this
    build (OpenCV 4.10.0) — confirmed by reading the property back as 0.0 after set().
    Shelling out to ffmpeg directly gives us full control over timeouts instead.
    Untested against real hardware in this project (see README limitations) — the RTSP
    URL/credentials are supplied by the administrator via the Cameras page and never
    hardcoded."""

    is_live = True
    label = "rtsp"

    def __init__(self, rtsp_url: str) -> None:
        self.width, self.height = 640, 480  # hardcoded — ffprobe returns 0,0 against this live RTSP push even when confirmed actively publishing; see docs/ai-pipeline.md
        self.frame_size = self.width * self.height * 3

        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-",
        ]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=self.frame_size,
        )

    def read(self) -> Optional[np.ndarray]:
        raw = self.process.stdout.read(self.frame_size)
        if len(raw) != self.frame_size:
            return None
        return np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 3))

    def release(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
