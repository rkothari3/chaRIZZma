"""
Real-time Audio AI based on official Google Gemini Live API example
Adapted to use Pi's audio stream instead of local microphone
"""

import asyncio
import sys
import traceback
import requests
import time

import pyaudio

import os
from google import genai

# Set API key before creating client
os.environ['GOOGLE_API_KEY'] = "AIzaSyC9_QNT5xBMh3s8BySrI7EAqu6DgdFYDLM"

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "gemini-live-2.5-flash-preview"

# Initialize client properly
client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'], http_options={"api_version": "v1beta"})

CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": "You are a helpful AI assistant. Always respond in clear English. Keep responses conversational, friendly, and under 8 seconds. Speak clearly and at a normal pace."
}

pya = pyaudio.PyAudio()

class PiAudioAI:
    def __init__(self, pi_ip="143.215.189.141"):
        self.pi_ip = pi_ip
        self.pi_audio_url = f"http://{pi_ip}:5001/audio_feed"
        
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        
        # For Pi audio streaming
        self.pi_stream_response = None
        
    async def capture_from_pi(self):
        """
        Continuously capture audio from Pi's stream and put in output queue
        Pi sends WAV format, we need to strip header and send raw PCM
        """
        print(f"🎤 Connecting to Pi audio stream: {self.pi_audio_url}")
        
        try:
            # Connect to Pi's audio stream
            self.pi_stream_response = requests.get(
                self.pi_audio_url, 
                stream=True, 
                timeout=None  # Keep connection open
            )
            
            if self.pi_stream_response.status_code != 200:
                print(f"❌ Failed to connect to Pi stream: {self.pi_stream_response.status_code}")
                return
            
            print("✅ Connected to Pi audio stream")
            
            # Skip WAV header (44 bytes) from first chunk
            header_skipped = False
            
            # Stream audio chunks continuously
            for chunk in self.pi_stream_response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    # Skip WAV header from first chunk
                    if not header_skipped:
                        if len(chunk) > 44:
                            chunk = chunk[44:]  # Remove WAV header
                            header_skipped = True
                            print("📝 Stripped WAV header, sending raw PCM")
                        else:
                            continue  # Skip if chunk too small to contain header
                    
                    # Put raw PCM audio data in queue
                    await self.out_queue.put({
                        "data": chunk, 
                        "mime_type": "audio/pcm"
                    })
                    
        except Exception as e:
            print(f"❌ Pi audio capture error: {e}")
    
    async def send_realtime(self):
        """Send audio from queue to Gemini (updated to new API)"""
        while True:
            msg = await self.out_queue.get()
            # Use the new send_realtime_input method
            if msg.get("mime_type") == "audio/pcm":
                await self.session.send_realtime_input(
                    audio={"data": msg["data"], "mime_type": "audio/pcm;rate=16000"}
                )
            else:
                # For other types of input (text, etc)
                await self.session.send_client_content(turns={"parts": [msg]})
    
    async def receive_audio(self):
        """Receive audio from Gemini - improved to prevent cutting off"""
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        print("🎵", end="")  # Show audio chunks being received
                        continue
                    if text := response.text:
                        print(f"\n🤖 Gemini says: {text}")
                        continue
                    
                    # Check for turn completion
                    if (hasattr(response, 'server_content') and 
                        response.server_content and 
                        hasattr(response.server_content, 'turn_complete') and 
                        response.server_content.turn_complete):
                        print("\n✅ Turn complete - audio should finish playing")
                        break
                
            except Exception as e:
                print(f"\n❌ Receive error: {e}")
                await asyncio.sleep(1)
    
    async def play_audio(self):
        """Play audio responses - improved to prevent cutting off"""
        print("🔊 Audio output initialized")
        
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE * 2  # Bigger buffer to prevent cutting
            )
            
            while True:
                try:
                    bytestream = await self.audio_in_queue.get()
                    if bytestream:
                        await asyncio.to_thread(stream.write, bytestream)
                        print("🔊", end="")  # Show audio being played
                except Exception as e:
                    print(f"\n❌ Audio play error: {e}")
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            print(f"\n❌ Audio stream error: {e}")
    
    async def send_text(self):
        """Optional text input (updated to new API)"""
        while True:
            text = await asyncio.to_thread(input, "Type message (or 'q' to quit): ")
            if text.lower() == "q":
                break
            await self.session.send_client_content(
                turns={"role": "user", "parts": [{"text": text or "."}]}, 
                turn_complete=True
            )
    
    async def run(self):
        """Main run loop (adapted from original example)"""
        print("🚀 Pi Audio AI Starting...")
        print("Make sure your Pi's audio_only.py is running")
        print("This will continuously process audio from Pi and respond with voice")
        print("Type 'q' in the text input to quit\n")
        
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                
                # Initialize queues
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                
                # Create all tasks (following original pattern)
                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.capture_from_pi())  # Our Pi audio capture
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                
                # Wait for user to quit
                await send_text_task
                raise asyncio.CancelledError("User requested exit")
                
        except asyncio.CancelledError:
            print("\n🛑 Shutting down...")
            if self.pi_stream_response:
                self.pi_stream_response.close()
        except ExceptionGroup as EG:
            print("\n❌ Error occurred:")
            traceback.print_exception(EG)

async def main():
    ai = PiAudioAI(pi_ip="143.215.189.141")  # Your Pi's IP
    await ai.run()

if __name__ == "__main__":
    asyncio.run(main())