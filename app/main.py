"""Main FastAPI application for real-time AI camera analytics."""

import asyncio
import base64
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.ai_analyzer import AIAnalyzer
from app.config import SAMPLE_STREAMS, settings
from app.stream_capture import StreamCapture

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
stream_capture: Optional[StreamCapture] = None
ai_analyzer: Optional[AIAnalyzer] = None
connected_clients: set[WebSocket] = set()
processing_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global ai_analyzer
    ai_analyzer = AIAnalyzer()
    logger.info("AI Analyzer initialized")
    if settings.roboflow_api_key:
        logger.info(f"Using Roboflow model: {settings.roboflow_model_id}")
    else:
        logger.info("No Roboflow API key set - running in DEMO mode with local analysis")
    yield
    # Cleanup
    if stream_capture:
        stream_capture.stop()


app = FastAPI(
    title="Real-Time AI Camera Analytics",
    description="Analyze live camera streams with AI-powered object detection",
    version="1.0.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "streams": SAMPLE_STREAMS,
            "has_api_key": bool(settings.roboflow_api_key),
        },
    )


@app.get("/api/streams")
async def get_streams():
    """Get list of available camera streams."""
    return {"streams": SAMPLE_STREAMS}


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    stream_status = stream_capture.get_status() if stream_capture else {"is_running": False}
    analytics = ai_analyzer.get_analytics() if ai_analyzer else {}
    return {
        "stream": stream_status,
        "analytics": analytics,
        "has_api_key": bool(settings.roboflow_api_key),
        "model": settings.roboflow_model_id,
    }


@app.post("/api/stream/start")
async def start_stream(body: dict):
    """Start capturing from a camera stream."""
    global stream_capture, processing_task

    url = body.get("url", "")
    stream_type = body.get("type", "auto")

    if not url:
        return {"error": "Stream URL is required"}

    # Stop existing stream
    if stream_capture and stream_capture.is_running:
        stream_capture.stop()
        if processing_task:
            processing_task.cancel()

    # Reset analytics
    if ai_analyzer:
        ai_analyzer.reset_analytics()

    stream_capture = StreamCapture(url, stream_type)
    success = await asyncio.get_event_loop().run_in_executor(None, stream_capture.start)

    if success:
        processing_task = asyncio.create_task(_process_stream())
        return {"status": "started", "message": "Stream connected successfully"}
    else:
        return {"error": "Failed to connect to stream. Check the URL and try again."}


@app.post("/api/stream/stop")
async def stop_stream():
    """Stop the current stream."""
    global stream_capture, processing_task

    if processing_task:
        processing_task.cancel()
        processing_task = None

    if stream_capture:
        stream_capture.stop()
        stream_capture = None

    return {"status": "stopped"}


@app.get("/api/analytics")
async def get_analytics():
    """Get current analytics data."""
    if ai_analyzer:
        return ai_analyzer.get_analytics()
    return {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time frame streaming."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")

    try:
        while True:
            # Keep connection alive, receive any control messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")


async def _process_stream():
    """Background task to process stream frames and broadcast results."""
    global stream_capture, ai_analyzer

    frame_skip = settings.frame_skip
    frame_idx = 0

    while stream_capture and stream_capture.is_running:
        try:
            frame = await stream_capture.read_frame_async()
            if frame is None:
                await asyncio.sleep(0.1)
                continue

            frame_idx += 1
            if frame_idx % frame_skip != 0:
                await asyncio.sleep(0.01)
                continue

            # Run AI analysis
            if ai_analyzer:
                result = ai_analyzer.analyze_frame(frame)

                if not result.get("skipped", False) and connected_clients:
                    # Draw detections on frame
                    annotated_frame = _draw_detections(frame, result)

                    # Encode frame as JPEG
                    _, buffer = cv2.imencode(
                        ".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70]
                    )
                    frame_b64 = base64.b64encode(buffer).decode("utf-8")

                    # Prepare message
                    message = {
                        "type": "frame",
                        "frame": frame_b64,
                        "detections": result.get("detections", []),
                        "frame_counts": result.get("frame_counts", {}),
                        "analytics": ai_analyzer.get_analytics(),
                        "stream_fps": round(stream_capture.fps, 1) if stream_capture else 0,
                    }

                    # Broadcast to all connected clients
                    import json

                    msg_str = json.dumps(message)
                    disconnected = set()
                    for client in connected_clients:
                        try:
                            await client.send_text(msg_str)
                        except Exception:
                            disconnected.add(client)

                    connected_clients.difference_update(disconnected)

            await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error processing stream: {e}")
            await asyncio.sleep(1)


def _draw_detections(frame: np.ndarray, result: dict) -> np.ndarray:
    """Draw bounding boxes and labels on the frame."""
    annotated = frame.copy()
    detections = result.get("detections", [])

    # Color map for different classes
    colors = {
        "person": (0, 255, 0),
        "car": (255, 0, 0),
        "truck": (255, 128, 0),
        "bus": (255, 0, 255),
        "bicycle": (0, 255, 255),
        "motorcycle": (128, 0, 255),
    }
    default_color = (0, 200, 200)

    for det in detections:
        cls = det.get("class", "unknown")
        conf = det.get("confidence", 0)
        x = int(det.get("x", 0))
        y = int(det.get("y", 0))
        w = int(det.get("width", 0))
        h = int(det.get("height", 0))
        track_id = det.get("track_id")

        # Calculate bbox corners
        x1 = x - w // 2
        y1 = y - h // 2
        x2 = x + w // 2
        y2 = y + h // 2

        color = colors.get(cls, default_color)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Draw label
        label = f"{cls} {conf:.0%}"
        if track_id:
            label += f" #{track_id}"

        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            annotated,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            color,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    # Draw frame info overlay
    height, width = annotated.shape[:2]
    info_text = f"Detections: {len(detections)}"
    cv2.putText(annotated, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    return annotated


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
