"""
Turn-based Audio AI - Fixed to prevent voice cutting off
Properly waits for complete responses before next turn
"""

import asyncio
import sys
import traceback
import requests
import time
import os

import pyaudio

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PI_IP = os.getenv('PI_IP', '143.215.189.141')

if not GOOGLE_API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    print("Make sure you have a .env file with your API key")
    exit(1)

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "gemini-live-2.5-flash-preview"

client = genai.Client(api_key=GOOGLE_API_KEY)

CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": "You are a helpful AI assistant. Always respond in clear English. Keep responses conversational, friendly, and complete. Speak at a normal pace and finish your thoughts."
}

pya = pyaudio.PyAudio()

class TurnBasedAudioAI:
    def __init__(self, pi_ip=None):
        self.pi_ip = pi_ip or PI_IP
        self.pi_audio_url = f"http://{self.pi_ip}:5001/audio_feed"
        
        # Turn control
        self.is_listening = False
        self.is_playing = False
        self.session = None
        
    def capture_audio_chunk(self, duration=4):
        """Capture a single chunk of audio from Pi - NOT continuous"""
        try:
            print(f"🎤 Listening for {duration} seconds...")
            self.is_listening = True
            
            response = requests.get(self.pi_audio_url, stream=True, timeout=10)
            if response.status_code != 200:
                print(f"❌ Can't connect to Pi")
                return None
            
            # Calculate bytes needed
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
                    
                    # Stop when we have enough OR timeout
                    if len(audio_data) >= bytes_needed:
                        break
                    if time.time() - start_time > duration + 2:
                        break
            
            self.is_listening = False
            print(f"✅ Captured {len(audio_data)} bytes")
            return audio_data[:bytes_needed]
            
        except Exception as e:
            self.is_listening = False
            print(f"❌ Capture error: {e}")
            return None
    
    async def process_and_play_response(self, audio_data):
        """Process audio with Gemini and play complete response"""
        try:
            print("🤖 Sending to Gemini...")
            
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                # Send audio
                await session.send_realtime_input(
                    audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
                )
                
                print("🎧 Receiving response...")
                
                # Collect ALL audio before playing
                complete_response = b""
                response_text = ""
                
                turn = session.receive()
                async for response in turn:
                    if response.data:
                        complete_response += response.data
                        print("📦", end="")  # Show chunks being collected
                    if response.text:
                        response_text += response.text
                
                # Now we have the COMPLETE response
                print(f"\n🤖 Gemini says: {response_text}")
                print(f"🎵 Playing complete response ({len(complete_response)} bytes)")
                
                if complete_response:
                    await self.play_complete_audio(complete_response)
                else:
                    print("❌ No audio received from Gemini")
                    
        except Exception as e:
            print(f"❌ Processing error: {e}")
    
    async def play_complete_audio(self, audio_data):
        """Play complete audio response without interruption"""
        try:
            self.is_playing = True
            print("🔊 Playing response...")
            
            # Open audio stream
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE * 4  # Large buffer
            )
            
            # Play audio in chunks
            bytes_played = 0
            while bytes_played < len(audio_data):
                chunk_end = min(bytes_played + CHUNK_SIZE, len(audio_data))
                chunk = audio_data[bytes_played:chunk_end]
                
                if chunk:
                    await asyncio.to_thread(stream.write, chunk)
                    bytes_played = chunk_end
                    print("🔊", end="")
            
            # Close stream and wait a moment for final audio to finish
            await asyncio.to_thread(stream.close)
            await asyncio.sleep(0.5)  # Let audio finish
            
            self.is_playing = False
            print("\n✅ Audio playback complete!")
            
        except Exception as e:
            self.is_playing = False
            print(f"\n❌ Playback error: {e}")
    
    async def conversation_loop(self):
        """Manual conversation loop - press key to start each turn"""
        print("🚀 Manual Audio AI Started!")
        print("🔑 Press ENTER to start listening for each turn")
        print("🛑 Press Ctrl+C to stop\n")
        
        turn_number = 1
        
        try:
            while True:
                print(f"\n{'='*60}")
                print(f"🔄 TURN {turn_number}")
                print(f"{'='*60}")
                
                # WAIT for user to press Enter
                user_input = await asyncio.to_thread(
                    input, 
                    "👆 Press ENTER to start listening (or type 'q' to quit): "
                )
                
                if user_input.lower() == 'q':
                    print("🛑 Quitting...")
                    break
                
                # STEP 1: Listen
                print("🎤 Starting to listen...")
                audio_data = self.capture_audio_chunk(duration=4)
                if not audio_data:
                    print("❌ No audio captured, try again!")
                    continue
                
                # STEP 2: Process and Play (complete response)
                await self.process_and_play_response(audio_data)
                
                # STEP 3: Wait for audio to completely finish
                print("🎵 Response complete! Ready for next turn.")
                turn_number += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Conversation ended")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

async def main():
    ai = TurnBasedAudioAI()  # Uses PI_IP from .env
    await ai.conversation_loop()

if __name__ == "__main__":
    asyncio.run(main())