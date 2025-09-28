"""
Video Sentiment Analysis with Gemini LIVE API
Combines Pi's video + audio streams for facial emotion recognition
"""

import asyncio
import base64
import io
import os
import sys
import traceback
import requests
import time
import cv2
import numpy as np
from PIL import Image

import pyaudio

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PI_IP = os.getenv('PI_IP', '143.215.189.141')

if not GOOGLE_API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    exit(1)

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "gemini-live-2.5-flash-preview"

client = genai.Client(api_key=GOOGLE_API_KEY, http_options={"api_version": "v1beta"})

CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": """You are an empathetic AI assistant that can see and hear the user. 
    Analyze their facial expressions, body language, and voice tone to understand their emotional state.
    Respond with appropriate emotional intelligence - be supportive if they seem sad, 
    celebratory if happy, calming if stressed, etc. 
    Keep responses under 8 seconds and always acknowledge what you observe about their mood."""
}

pya = pyaudio.PyAudio()

class VideoSentimentAI:
    def __init__(self):
        self.pi_video_url = f"http://{PI_IP}:5000/video_feed"
        self.pi_audio_url = f"http://{PI_IP}:5001/audio_feed"
        
        # Queues for streaming
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        
        # Video streaming
        self.video_stream_response = None
        self.audio_stream_response = None
        
        # Control flags
        self.is_running = False
        
    def capture_frame_from_pi_stream(self):
        """Capture a single frame from Pi's video stream"""
        try:
            # Get a single frame from the MJPEG stream
            response = requests.get(self.pi_video_url, stream=True, timeout=5)
            if response.status_code != 200:
                print(f"❌ Can't connect to Pi video stream")
                return None
            
            # Parse MJPEG stream to extract one frame
            bytes_data = b""
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                
                # Look for JPEG frame boundaries
                start = bytes_data.find(b'\xff\xd8')  # JPEG start marker
                end = bytes_data.find(b'\xff\xd9')    # JPEG end marker
                
                if start != -1 and end != -1:
                    # Extract complete JPEG frame
                    jpeg_bytes = bytes_data[start:end+2]
                    
                    # Convert to image and process
                    return self.process_frame_for_gemini(jpeg_bytes)
            
            return None
            
        except Exception as e:
            print(f"❌ Video capture error: {e}")
            return None
    
    def process_frame_for_gemini(self, jpeg_bytes):
        """Process frame for Gemini LIVE API (similar to official example)"""
        try:
            # Convert JPEG bytes to PIL Image
            img = Image.open(io.BytesIO(jpeg_bytes))
            
            # Resize for efficiency (following official example)
            img.thumbnail([1024, 1024])
            
            # Convert back to JPEG bytes
            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)
            
            mime_type = "image/jpeg"
            image_bytes = image_io.read()
            
            return {
                "mime_type": mime_type, 
                "data": base64.b64encode(image_bytes).decode()
            }
            
        except Exception as e:
            print(f"❌ Frame processing error: {e}")
            return None
    
    async def capture_pi_streams(self):
        """Capture both video and audio from Pi streams - manual trigger"""
        try:
            print("📹 Attempting to capture video frame from Pi...")
            
            # Try to get video frame (optional - continue if fails)
            video_frame = await asyncio.to_thread(self.capture_frame_from_pi_stream)
            if video_frame:
                await self.out_queue.put(video_frame)
                print("✅ Video frame captured and queued")
            else:
                print("⚠️ Video capture failed - continuing with audio-only analysis")
                print("💡 Make sure Pi's video stream is running: python usb_cam_stream.py")
            
            print("🎤 Capturing 4 seconds of audio from Pi...")
            
            # Get audio chunk (required for analysis)
            audio_data = await self.capture_audio_chunk_from_pi()
            if audio_data:
                await self.out_queue.put({
                    "data": audio_data, 
                    "mime_type": "audio/pcm"
                })
                print("✅ Audio captured and queued")
                return True  # Success - at least have audio
            else:
                print("❌ Failed to capture audio - cannot proceed")
                return False  # Failure - need at least audio
                
        except Exception as e:
            print(f"❌ Stream capture error: {e}")
            return False
    
    async def capture_audio_chunk_from_pi(self, duration=4):
        """Capture audio chunk from Pi (adapted from turn_based_audio_ai.py)"""
        try:
            response = requests.get(self.pi_audio_url, stream=True, timeout=10)
            if response.status_code != 200:
                return None
            
            bytes_needed = SEND_SAMPLE_RATE * CHANNELS * 2 * duration
            audio_data = b""
            header_skipped = False
            start_time = time.time()
            
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    # Skip WAV header from first chunk
                    if not header_skipped:
                        if len(chunk) > 44:
                            chunk = chunk[44:]
                            header_skipped = True
                        else:
                            continue
                    
                    audio_data += chunk
                    
                    if len(audio_data) >= bytes_needed:
                        break
                    if time.time() - start_time > duration + 2:
                        break
            
            return audio_data[:bytes_needed]
            
        except Exception as e:
            print(f"❌ Audio capture error: {e}")
            return None
    
    async def send_realtime(self):
        """Send captured data to Gemini (using official API method)"""
        while self.is_running:
            try:
                msg = await asyncio.wait_for(self.out_queue.get(), timeout=1.0)
                
                # Use the same method as official example - session.send with input parameter
                await self.session.send(input=msg)
                
                # Log what was sent based on message type
                if msg.get("mime_type") == "audio/pcm":
                    print("📤 Audio sent to Gemini")
                elif msg.get("mime_type") == "image/jpeg":
                    print("📤 Image sent to Gemini") 
                else:
                    print(f"📤 Data sent to Gemini: {msg.get('mime_type', 'unknown')}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Send error: {e}")
    
    async def receive_audio(self):
        """Receive audio responses from Gemini (from official example)"""
        while self.is_running:
            try:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        print("🎵", end="")
                        continue
                    if text := response.text:
                        print(f"\n🤖 Sentiment Analysis: {text}")
                
                # Clear queue on turn complete
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
                    
            except Exception as e:
                print(f"❌ Receive error: {e}")
                await asyncio.sleep(1)
    
    async def play_audio(self):
        """Play audio responses (from official example)"""
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        
        while self.is_running:
            try:
                bytestream = await asyncio.wait_for(self.audio_in_queue.get(), timeout=1.0)
                await asyncio.to_thread(stream.write, bytestream)
                print("🔊", end="")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Playback error: {e}")
    
    async def manual_sentiment_analysis(self):
        """Manual trigger for video + audio sentiment analysis"""
        print("🚀 Video Sentiment AI Started!")
        print("📹 Analyzes your face + voice for emotional state")
        print("🔑 Press ENTER to capture video + audio for analysis")
        print("🛑 Type 'q' to quit\n")
        
        analysis_number = 1
        
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.is_running = True
                
                # Initialize queues
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=10)
                
                # Start background tasks
                tg.create_task(self.send_realtime())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                
                # Manual trigger loop
                while True:
                    print(f"\n{'='*60}")
                    print(f"🎭 SENTIMENT ANALYSIS #{analysis_number}")
                    print(f"{'='*60}")
                    
                    user_input = await asyncio.to_thread(
                        input, 
                        "👆 Press ENTER to analyze your mood (or 'q' to quit): "
                    )
                    
                    if user_input.lower() == 'q':
                        break
                    
                    # Capture both video and audio
                    print("📸 Capturing video + audio for sentiment analysis...")
                    success = await self.capture_pi_streams()
                    
                    if not success:
                        print("❌ Could not capture streams - skipping this analysis")
                        continue
                    
                    print("🧠 Gemini is analyzing your emotional state...")
                    print("🔊 Listen for the empathetic response!")
                    
                    # Wait a moment for processing
                    await asyncio.sleep(5)  # Give more time for processing
                    analysis_number += 1
                
                self.is_running = False
                
        except KeyboardInterrupt:
            print("\n🛑 Sentiment analysis stopped")
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()

async def main():
    # Check if required packages are installed
    try:
        import cv2, PIL
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("pip install opencv-python pillow")
        return
    
    ai = VideoSentimentAI()
    await ai.manual_sentiment_analysis()

if __name__ == "__main__":
    asyncio.run(main())