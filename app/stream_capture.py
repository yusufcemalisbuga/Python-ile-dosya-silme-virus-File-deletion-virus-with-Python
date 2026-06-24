"""Stream capture module for connecting to public camera feeds."""

import asyncio
import logging
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class StreamCapture:
    """Captures frames from various video stream sources."""

    def __init__(self, stream_url: str, stream_type: str = "auto"):
        self.stream_url = stream_url
        self.stream_type = stream_type
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_count = 0
        self.fps = 0.0
        self._last_fps_time = time.time()
        self._fps_frame_count = 0

    def _resolve_stream_url(self) -> str:
        """Resolve the actual stream URL (e.g., for YouTube streams)."""
        url = self.stream_url

        if self.stream_type == "youtube" or "youtube.com" in url or "youtu.be" in url:
            try:
                import subprocess

                result = subprocess.run(
                    ["yt-dlp", "--get-url", "-f", "best[height<=480]", url],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                # Try without format filter
                result = subprocess.run(
                    ["yt-dlp", "--get-url", "-f", "best", url],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"yt-dlp failed: {e}. Using URL directly.")

        return url

    def start(self) -> bool:
        """Start capturing from the stream."""
        try:
            resolved_url = self._resolve_stream_url()
            logger.info(f"Connecting to stream: {resolved_url[:100]}...")

            self.cap = cv2.VideoCapture(resolved_url)

            if not self.cap.isOpened():
                logger.error(f"Failed to open stream: {self.stream_url}")
                return False

            # Set buffer size to minimum for real-time
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.is_running = True
            self.frame_count = 0
            self._last_fps_time = time.time()
            self._fps_frame_count = 0
            logger.info("Stream connected successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            return False

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from the stream."""
        if not self.is_running or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to read frame, attempting reconnect...")
            self.stop()
            if self.start():
                ret, frame = self.cap.read()
                if not ret:
                    return None
            else:
                return None

        self.frame_count += 1
        self._fps_frame_count += 1

        # Calculate FPS every second
        current_time = time.time()
        elapsed = current_time - self._last_fps_time
        if elapsed >= 1.0:
            self.fps = self._fps_frame_count / elapsed
            self._fps_frame_count = 0
            self._last_fps_time = current_time

        return frame

    async def read_frame_async(self) -> Optional[np.ndarray]:
        """Async wrapper for reading frames."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_frame)

    def stop(self):
        """Stop the stream capture."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Stream capture stopped")

    def get_status(self) -> dict:
        """Get current stream status."""
        return {
            "is_running": self.is_running,
            "frame_count": self.frame_count,
            "fps": round(self.fps, 1),
            "stream_url": self.stream_url,
        }
