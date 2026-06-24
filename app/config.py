"""Configuration settings for the real-time AI camera analytics system."""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    roboflow_api_key: str = field(
        default_factory=lambda: os.getenv("ROBOFLOW_API_KEY", "")
    )
    roboflow_model_id: str = field(
        default_factory=lambda: os.getenv("ROBOFLOW_MODEL_ID", "yolov8n-640")
    )
    roboflow_model_version: str = field(
        default_factory=lambda: os.getenv("ROBOFLOW_MODEL_VERSION", "1")
    )

    # Detection confidence threshold
    confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))
    )

    # Frame processing settings
    frame_skip: int = field(
        default_factory=lambda: int(os.getenv("FRAME_SKIP", "3"))
    )
    max_fps: int = field(
        default_factory=lambda: int(os.getenv("MAX_FPS", "10"))
    )

    # Server settings
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))


# Sample public camera streams (legal, publicly accessible)
SAMPLE_STREAMS = [
    {
        "name": "Jackson Hole Town Square",
        "url": "https://www.youtube.com/watch?v=1EiC9bvVGnk",
        "type": "youtube",
        "description": "Live view of Jackson Hole, Wyoming town square",
    },
    {
        "name": "Abbey Road Crossing (London)",
        "url": "https://www.youtube.com/watch?v=S22w05dHfOA",
        "type": "youtube",
        "description": "The famous Beatles Abbey Road crossing",
    },
    {
        "name": "Times Square NYC",
        "url": "https://www.youtube.com/watch?v=AdUw5RdyZxI",
        "type": "youtube",
        "description": "Live Times Square camera feed",
    },
    {
        "name": "Venice Beach Boardwalk",
        "url": "https://www.youtube.com/watch?v=ZzlNGOc2IzM",
        "type": "youtube",
        "description": "Live Venice Beach boardwalk camera",
    },
    {
        "name": "Traffic Cam - Sample MJPEG",
        "url": "http://pendelcam.kip.uni-heidelberg.de/mjpg/video.mjpg",
        "type": "mjpeg",
        "description": "University of Heidelberg pendulum camera (MJPEG)",
    },
    {
        "name": "Custom Stream",
        "url": "",
        "type": "custom",
        "description": "Enter your own RTSP/MJPEG/HTTP stream URL",
    },
]


settings = Settings()
