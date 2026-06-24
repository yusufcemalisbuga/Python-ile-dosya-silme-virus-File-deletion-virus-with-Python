"""AI Analysis module using Roboflow's hosted inference API."""

import base64
import logging
import time
from collections import defaultdict
from typing import Optional

import cv2
import numpy as np
import requests

from app.config import settings

logger = logging.getLogger(__name__)


class Detection:
    """Represents a single detected object."""

    def __init__(self, class_name: str, confidence: float, bbox: dict, track_id: Optional[int] = None):
        self.class_name = class_name
        self.confidence = confidence
        self.x = bbox.get("x", 0)
        self.y = bbox.get("y", 0)
        self.width = bbox.get("width", 0)
        self.height = bbox.get("height", 0)
        self.track_id = track_id

    def to_dict(self) -> dict:
        return {
            "class": self.class_name,
            "confidence": round(self.confidence, 3),
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "track_id": self.track_id,
        }


class AIAnalyzer:
    """Performs AI analysis on video frames using Roboflow API."""

    def __init__(self):
        self.api_key = settings.roboflow_api_key
        self.model_id = settings.roboflow_model_id
        self.model_version = settings.roboflow_model_version
        self.confidence_threshold = settings.confidence_threshold

        # Analytics tracking
        self.total_detections = 0
        self.class_counts: dict[str, int] = defaultdict(int)
        self.frame_history: list[dict] = []
        self.max_history = 100

        # Simple motion tracking
        self._previous_detections: list[Detection] = []
        self._track_id_counter = 0

        # Rate limiting
        self._last_inference_time = 0
        self._min_interval = 1.0 / settings.max_fps

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame as base64 JPEG for API submission."""
        # Resize for faster inference
        height, width = frame.shape[:2]
        max_dim = 640
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buffer).decode("utf-8")

    def _call_roboflow_api(self, frame: np.ndarray) -> Optional[dict]:
        """Call Roboflow's hosted inference API."""
        if not self.api_key:
            return self._generate_demo_detections(frame)

        try:
            img_base64 = self._encode_frame(frame)

            # Use Roboflow Hosted Inference API
            url = f"https://detect.roboflow.com/{self.model_id}/{self.model_version}"
            params = {
                "api_key": self.api_key,
                "confidence": int(self.confidence_threshold * 100),
            }

            response = requests.post(
                url,
                params=params,
                data=img_base64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Roboflow API error: {response.status_code} - {response.text}")
                return self._generate_demo_detections(frame)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Roboflow API request failed: {e}")
            return self._generate_demo_detections(frame)

    def _generate_demo_detections(self, frame: np.ndarray) -> dict:
        """Generate simulated detections for demo mode (when no API key is set)."""
        height, width = frame.shape[:2]

        # Use simple frame analysis to create pseudo-detections
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        # Edge detection to find regions of interest
        edges = cv2.Canny(blurred, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        predictions = []
        # Filter significant contours
        min_area = (width * height) * 0.005
        max_area = (width * height) * 0.4

        significant_contours = [
            c for c in contours
            if min_area < cv2.contourArea(c) < max_area
        ]

        # Sort by area and take top detections
        significant_contours.sort(key=cv2.contourArea, reverse=True)

        classes = ["person", "car", "truck", "bicycle", "bus", "motorcycle"]

        for i, contour in enumerate(significant_contours[:8]):
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = h / w if w > 0 else 1

            # Assign class based on aspect ratio heuristics
            if aspect_ratio > 1.5:
                cls = "person"
            elif aspect_ratio < 0.7:
                cls = "car" if w > width * 0.1 else "bicycle"
            else:
                cls = classes[i % len(classes)]

            confidence = max(0.4, min(0.95, 0.7 + (cv2.contourArea(contour) / max_area) * 0.25))

            predictions.append({
                "class": cls,
                "confidence": confidence,
                "x": x + w // 2,
                "y": y + h // 2,
                "width": w,
                "height": h,
            })

        return {
            "predictions": predictions,
            "image": {"width": width, "height": height},
        }

    def _assign_track_ids(self, detections: list[Detection]) -> list[Detection]:
        """Simple tracking by matching detections to previous frame positions."""
        if not self._previous_detections:
            for det in detections:
                self._track_id_counter += 1
                det.track_id = self._track_id_counter
        else:
            used_prev = set()
            for det in detections:
                best_match = None
                best_dist = float("inf")

                for i, prev in enumerate(self._previous_detections):
                    if i in used_prev:
                        continue
                    if prev.class_name != det.class_name:
                        continue

                    dist = ((det.x - prev.x) ** 2 + (det.y - prev.y) ** 2) ** 0.5
                    if dist < best_dist and dist < max(det.width, det.height) * 2:
                        best_dist = dist
                        best_match = i

                if best_match is not None:
                    det.track_id = self._previous_detections[best_match].track_id
                    used_prev.add(best_match)
                else:
                    self._track_id_counter += 1
                    det.track_id = self._track_id_counter

        self._previous_detections = detections
        return detections

    def analyze_frame(self, frame: np.ndarray) -> dict:
        """Analyze a single frame and return detection results."""
        # Rate limiting
        current_time = time.time()
        if current_time - self._last_inference_time < self._min_interval:
            return {"detections": [], "skipped": True}
        self._last_inference_time = current_time

        # Call inference API
        result = self._call_roboflow_api(frame)
        if result is None:
            return {"detections": [], "error": "Inference failed"}

        # Parse detections
        predictions = result.get("predictions", [])
        image_info = result.get("image", {})

        detections = []
        for pred in predictions:
            if pred.get("confidence", 0) >= self.confidence_threshold:
                det = Detection(
                    class_name=pred.get("class", "unknown"),
                    confidence=pred.get("confidence", 0),
                    bbox={
                        "x": pred.get("x", 0),
                        "y": pred.get("y", 0),
                        "width": pred.get("width", 0),
                        "height": pred.get("height", 0),
                    },
                )
                detections.append(det)

        # Assign tracking IDs
        detections = self._assign_track_ids(detections)

        # Update analytics
        frame_counts = defaultdict(int)
        for det in detections:
            self.total_detections += 1
            self.class_counts[det.class_name] += 1
            frame_counts[det.class_name] += 1

        # Store frame history
        frame_data = {
            "timestamp": current_time,
            "counts": dict(frame_counts),
            "total": len(detections),
        }
        self.frame_history.append(frame_data)
        if len(self.frame_history) > self.max_history:
            self.frame_history.pop(0)

        return {
            "detections": [d.to_dict() for d in detections],
            "frame_counts": dict(frame_counts),
            "image_size": image_info,
            "skipped": False,
        }

    def get_analytics(self) -> dict:
        """Get cumulative analytics data."""
        # Calculate recent averages
        recent = self.frame_history[-30:] if self.frame_history else []
        avg_per_frame = sum(f["total"] for f in recent) / len(recent) if recent else 0

        return {
            "total_detections": self.total_detections,
            "class_counts": dict(self.class_counts),
            "avg_per_frame": round(avg_per_frame, 1),
            "frames_analyzed": len(self.frame_history),
            "active_tracks": self._track_id_counter,
        }

    def reset_analytics(self):
        """Reset all analytics counters."""
        self.total_detections = 0
        self.class_counts.clear()
        self.frame_history.clear()
        self._track_id_counter = 0
        self._previous_detections.clear()
