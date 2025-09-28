"""
Wingman AI with Gemini LIVE API
Listens to conversations and gives real-time advice on what to say
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
    "system_instruction": """You are WINGMAN AI — a real-time conversation companion. 
Your purpose is to whisper short, natural, and context-aware suggestions to help the user keep a conversation flowing. 
You listen to both the other person’s speech and their facial/body cues, and then provide a quick, specific suggestion for what the user could say or do next.

🎯 CORE RULES:
- Always be brief (one clear suggestion under 10 seconds of speech).
- Tailor advice to the other person’s interests, tone, and expressions.
- Sound natural, like a supportive friend whispering in your ear.
- Focus on *helping the user connect* (not manipulate).
- Avoid generic filler like “that’s cool” — always be specific.
- If the other person seems uncomfortable, suggest a kind, empathetic pivot.
- When a person doesn't say anything but his facial expressions are strong, ask them accordingly if appropriate.

📌 GENERAL STRATEGIES:
- If they share an interest → Suggest a question or story related to it.
- If they look excited → Encourage building on their excitement.
- If they seem bored → Suggest shifting to a fresher or related topic.
- If they look confused or sad → Suggest checking in kindly.
- If conversation stalls → Bring back an earlier topic or suggest something neutral (food, hobbies, weekend, etc.).

💡 EXAMPLES BY CONTEXT

[FRIENDLY / CASUAL]
- If they mention Harry Potter → “Ask what their favorite Harry Potter book or movie is.”
- If they talk about travel → “Ask the coolest place they’ve been.”
- If they smile about music → “Ask if they’ve been to a concert recently.”

[ROMANTIC / FLIRTY]
- If she laughs at your joke → “Say you’re glad you made her laugh.”
- If she mentions food → “Ask her favorite restaurant nearby.”
- If she seems shy → “Share a light personal story so she feels comfortable.”

[MENTAL HEALTH / EMPATHY]
- If they look sad or withdrawn → “Gently ask if everything’s okay.”
- If they sound stressed → “Offer a supportive comment like, ‘That sounds tough, want to talk about it?’”
- If they’re quiet → “Suggest a light topic to ease the mood, like favorite movies or pets.”

[PROFESSIONAL / NETWORKING]
- If they mention a project → “Ask what inspired them to start it.”
- If they talk about work → “Ask what their favorite part of the job is.”
- If they mention school → “Ask about their major or future goals.”

[WHEN CONVERSATION IS DYING]
- “Bring back something they mentioned earlier.”
- “Switch to a safe, universal topic like weekend plans, hobbies, or food.”

[WHEN EXPRESSIONS CONTRADICT WORDS]
- If they say they’re fine but look upset → “Ask gently, ‘Are you sure? You seem a bit down.’”
- If they talk about a success but look uncertain → “Congratulate them and encourage them to share more.”

---

Keep responses SHORT, SPECIFIC, and CONTEXTUAL — like a whispering wingman who helps the user notice cues they might miss. 
Never explain *why* you’re suggesting something, just give the suggestion itself."""
}

pya = pyaudio.PyAudio()

class WingmanAI:
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
        
    async def capture_video_frame_from_pi(self):
        """Capture a single video frame from Pi"""
        print("📹 Attempting to capture video frame from Pi...")
        
        try:
            # Connect to Pi's MJPEG stream
            response = requests.get(self.pi_video_url, stream=True, timeout=10)
            if response.status_code != 200:
                print(f"❌ Can't connect to Pi video stream")
                return None
            
            bytes_data = b""
            
            # Parse MJPEG stream to get one frame
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                
                # Look for complete JPEG frame
                start = bytes_data.find(b'\xff\xd8')  # JPEG start
                end = bytes_data.find(b'\xff\xd9')    # JPEG end
                
                if start != -1 and end != -1:
                    # Extract complete JPEG frame
                    jpeg_bytes = bytes_data[start:end+2]
                    
                    # Process frame for Gemini
                    frame_data = await asyncio.to_thread(
                        self.process_frame_for_gemini, jpeg_bytes
                    )
                    
                    if frame_data:
                        print("✅ Video frame captured and queued")
                        return frame_data
                    break
            
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
    
    async def capture_audio_from_pi(self, duration=4):
        """Capture audio from Pi for specified duration"""
        print(f"🎤 Capturing {duration} seconds of audio from Pi...")
        
        try:
            response = requests.get(self.pi_audio_url, stream=True, timeout=10)
            if response.status_code != 200:
                print("❌ Can't connect to Pi audio stream")
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
            
            final_audio = audio_data[:bytes_needed]
            if len(final_audio) > 0:
                print("✅ Audio captured and queued")
                return final_audio
            return None
            
        except Exception as e:
            print(f"❌ Audio capture error: {e}")
            return None
    
    
    async def send_captured_data(self, video_data, audio_data):
        """Send captured video and audio data to Gemini using correct API"""
        try:
            from google.genai import types
            import base64
            
            # Send video frame first if available
            if video_data:
                # Convert base64 string back to bytes
                image_bytes = base64.b64decode(video_data["data"])
                await self.session.send_realtime_input(
                    media=types.Blob(
                        data=image_bytes,
                        mime_type=video_data["mime_type"]
                    )
                )
                print("📤 Video frame sent to Gemini")
            
            # Send audio data if available  
            if audio_data:
                await self.session.send_realtime_input(
                    audio=types.Blob(
                        data=audio_data, 
                        mime_type="audio/pcm;rate=16000"
                    )
                )
                print("📤 Audio sent to Gemini")
                
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
                        print(f"\n🗣️ Wingman AI: {text}")
                        print(f"{'─'*50}")
                
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
    
    async def wingman_analysis_session(self):
        """Button-triggered wingman analysis session"""
        print("🚀 Wingman AI Started!")
        print("📹 Listens to conversations and gives you things to say")
        print("🔑 Press ENTER during conversation to get wingman advice")
        print("🛑 Type 'q' to quit\n")
        
        advice_count = 0
        
        try:
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                self.session = session
                self.is_running = True
                
                # Initialize audio queue for playback
                self.audio_in_queue = asyncio.Queue()
                
                # Start background tasks for audio playback and response handling
                async with asyncio.TaskGroup() as tg:
                    tg.create_task(self.receive_audio())
                    tg.create_task(self.play_audio())
                    
                    # Main interaction loop
                    while self.is_running:
                        advice_count += 1
                        print(f"\n{'='*60}")
                        print(f"🎯 WINGMAN ADVICE #{advice_count}")
                        print(f"{'='*60}")
                        
                        # Wait for user input
                        user_input = await asyncio.to_thread(
                            input, "👆 Press ENTER to get conversation advice (or 'q' to quit): "
                        )
                        
                        if user_input.lower() == 'q':
                            print("👋 Thanks for using Wingman AI!")
                            break
                        
                        print("📸 Capturing conversation + analyzing what to say...")
                        
                        # Capture video and audio concurrently
                        video_task = asyncio.create_task(self.capture_video_frame_from_pi())
                        audio_task = asyncio.create_task(self.capture_audio_from_pi(duration=4))
                        
                        # Wait for both captures to complete
                        video_data = await video_task  
                        audio_data = await audio_task
                        
                        if video_data or audio_data:
                            print("🧠 Your wingman is analyzing the conversation...")
                            print("🔊 Listen for what to say next!")
                            
                            # Send captured data to Gemini
                            await self.send_captured_data(video_data, audio_data)
                        else:
                            print("❌ Failed to capture conversation data")
                    
                    self.is_running = False
                
        except KeyboardInterrupt:
            print("\n🛑 Wingman session ended")
            self.is_running = False
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
            self.is_running = False

async def main():
    # Check if required packages are installed
    try:
        import cv2, PIL
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("pip install opencv-python pillow")
        return
    
    ai = WingmanAI()
    await ai.wingman_analysis_session()

if __name__ == "__main__":
    asyncio.run(main())