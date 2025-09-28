# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies (if requirements.txt exists)
pip install flask opencv-python
```

### Running the Applications

**Video Streaming Service:**
```bash
python usb_cam_stream.py
# Runs on http://0.0.0.0:5000
# Endpoint: /video_feed
```

**Audio Streaming Service:**
```bash
python audio_only.py
# Runs on http://0.0.0.0:5001
# Endpoint: /audio_feed
```

## Architecture Overview

**chaRIZZma** is a multimedia streaming application providing separate audio and video streaming services using Flask.

### Core Components

- **`usb_cam_stream.py`**: Video streaming service using OpenCV to capture from USB camera (device 0) and stream MJPEG over HTTP
- **`audio_only.py`**: Audio streaming service using arecord to capture from hardware audio device (hw:1,0) and stream WAV format over HTTP

### Key Technical Details

**Video Streaming**: 
- Uses OpenCV VideoCapture for camera access
- Encodes frames as JPEG and streams via multipart HTTP response
- Default camera device: index 0

**Audio Streaming**:
- Uses subprocess to run `arecord` command for audio capture  
- Audio format: 16-bit PCM, 16kHz, mono
- Hardware device: `hw:1,0`
- Includes proper WAV header for browser compatibility
- Implements process management to handle stream restarts

**Network Configuration**:
- Video service: Port 5000
- Audio service: Port 5001
- Both bind to `0.0.0.0` (all interfaces)

### Dependencies
- **Flask**: Web framework for HTTP streaming endpoints
- **OpenCV (cv2)**: Camera capture and image processing
- **subprocess**: System process management for audio capture

## Hardware Requirements

- USB camera accessible as device 0
- Audio input device accessible as `hw:1,0`
- Linux environment with `arecord` utility installed


## For when the audio things starts tripping (ignore at most times)
// To clean
sudo lsof /dev/snd/*
pulseaudio --kill