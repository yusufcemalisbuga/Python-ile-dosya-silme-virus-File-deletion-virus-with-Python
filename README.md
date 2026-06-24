# Real-Time AI Camera Analytics

A web-based system that connects to legal public live camera feeds (street, square, traffic, or nature cameras) and analyzes streaming footage in real-time using cloud-based AI — powered by **Roboflow Universe** models.

No heavy software installation required — everything runs in a lightweight web browser dashboard.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red)
![Roboflow](https://img.shields.io/badge/Roboflow-AI--Powered-purple)

## Features

- **Live Camera Streams** — Connect to public MJPEG, RTSP, HLS, or YouTube live streams
- **AI Object Detection** — Real-time detection using Roboflow's hosted YOLOv8 models
- **Human/Vehicle Counting** — Automatic counting of people, cars, buses, trucks, bicycles
- **Motion Tracking** — Simple object tracking across frames with unique IDs
- **Web Dashboard** — Beautiful real-time dashboard with WebSocket streaming
- **Demo Mode** — Works without API key using local computer vision analysis
- **Analytics** — Cumulative statistics, detection logs, and per-frame metrics

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Web Browser                      │
│          (Dashboard + WebSocket Client)           │
└─────────────────────┬───────────────────────────┘
                      │ WebSocket (frames + detections)
┌─────────────────────┴───────────────────────────┐
│              FastAPI Backend                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────┐ │
│  │   Stream     │  │  AI Analyzer  │  │  API   │ │
│  │   Capture    │──│  (Roboflow)   │──│ Routes │ │
│  │  (OpenCV)    │  │              │  │        │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┘ │
└─────────┼────────────────┼──────────────────────┘
          │                │
┌─────────┴──────┐  ┌─────┴──────────────┐
│  Public Camera  │  │  Roboflow Cloud API │
│  Streams (IP)   │  │  (Object Detection) │
└────────────────┘  └────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

Or with yt-dlp for YouTube stream support:

```bash
pip install -e .
pip install yt-dlp
```

### 2. (Optional) Set Roboflow API Key

Get a free API key from [Roboflow Universe](https://universe.roboflow.com/):

```bash
export ROBOFLOW_API_KEY="your_api_key_here"
```

> **Note:** The system works in **Demo Mode** without an API key, using local OpenCV-based analysis.

### 3. Run the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at: **http://localhost:8000**

### 4. Select a Camera Stream

Choose from pre-configured public camera feeds or enter your own stream URL:
- YouTube Live streams
- MJPEG camera feeds
- RTSP streams
- HTTP video streams

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ROBOFLOW_API_KEY` | (empty) | Roboflow API key for cloud inference |
| `ROBOFLOW_MODEL_ID` | `yolov8n-640` | Model ID from Roboflow Universe |
| `ROBOFLOW_MODEL_VERSION` | `1` | Model version |
| `CONFIDENCE_THRESHOLD` | `0.4` | Minimum detection confidence (0-1) |
| `FRAME_SKIP` | `3` | Process every Nth frame |
| `MAX_FPS` | `10` | Maximum inference FPS |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## Using with Roboflow

1. Go to [Roboflow Universe](https://universe.roboflow.com/)
2. Find a pre-trained model (e.g., COCO object detection, traffic detection)
3. Get your API key from your Roboflow account
4. Set the model ID and version in environment variables

Popular models:
- `coco/3` — General object detection (80 classes)
- `vehicle-detection-3mmwj/1` — Vehicle-specific detection
- `people-detection-o4rdr/2` — People detection
- `traffic-and-road-signs/2` — Traffic sign detection

## Sample Public Camera Streams

The system comes pre-configured with legal, publicly accessible camera feeds:

| Camera | Location | Type |
|--------|----------|------|
| Jackson Hole Town Square | Wyoming, USA | YouTube Live |
| Abbey Road Crossing | London, UK | YouTube Live |
| Times Square | New York, USA | YouTube Live |
| Venice Beach Boardwalk | California, USA | YouTube Live |
| Heidelberg Pendulum | Germany | MJPEG |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check .

# Run tests
pytest

# Run with hot reload
uvicorn app.main:app --reload
```

## Tech Stack

- **Backend**: Python, FastAPI, OpenCV, NumPy
- **AI**: Roboflow Hosted Inference API (YOLOv8, etc.)
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Streaming**: WebSockets for real-time frame delivery
- **Stream Sources**: OpenCV VideoCapture (MJPEG, RTSP, HTTP, YouTube via yt-dlp)

## Legal Notice

This system is designed to work with **legally accessible, public camera feeds** only. Always ensure you have the right to access and analyze any camera stream you connect to. Do not use this system for surveillance or any illegal purpose.
