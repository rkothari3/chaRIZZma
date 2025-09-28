"""
Ultra-simple Audio AI processor based on official Gemini Live API examples
"""
import asyncio
import wave
import requests
import time
from google import genai
from google.genai import types

class SimpleAudioAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-live-2.5-flash-preview"  # Half-cascade model
        
        # Simple config - just audio output
        self.config = {
            "response_modalities": ["AUDIO"]
        }
    
    def capture_audio_from_pi(self, duration=3):
        """Capture audio from Pi's stream"""
        try:
            print(f"🎤 Capturing {duration}s audio from Pi...")
            
            # Connect to Pi's audio stream  
            response = requests.get("http://143.215.189.141:5001/audio_feed", 
                                  stream=True, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Can't connect to Pi audio stream")
                return None
            
            # Collect audio data
            audio_data = b""
            bytes_needed = 16000 * 1 * 2 * duration  # 16kHz, mono, 16-bit
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_data += chunk
                    if len(audio_data) >= bytes_needed:
                        break
            
            print(f"✅ Got {len(audio_data)} bytes of audio")
            return audio_data[:bytes_needed]
            
        except Exception as e:
            print(f"❌ Audio capture error: {e}")
            return None
    
    def save_wav_file(self, audio_data, filename, sample_rate=16000):
        """Save audio as WAV file"""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
    
    async def send_audio_to_gemini(self, audio_data):
        """Send audio to Gemini and get response - following the notebook pattern"""
        try:
            print("🤖 Sending to Gemini...")
            
            # Save input as WAV first (Gemini likes WAV format)
            self.save_wav_file(audio_data, "input.wav")
            
            # Upload the WAV file using Files API (easier than raw PCM)
            print("📁 Uploading audio file...")
            uploaded_file = self.client.files.upload(file="input.wav")
            
            print("🔄 Processing with Gemini...")
            # Use the simpler generateContent API instead of Live API WebSocket
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # Regular model for file uploads
                contents=[uploaded_file, "Listen to this audio and respond naturally. Keep it conversational."]
            )
            
            print(f"📝 Gemini text response: {response.text}")
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return None
    
    async def text_to_speech_gemini(self, text):
        """Convert text to speech using Live API"""
        try:
            print("🔊 Converting to speech...")
            
            async with self.client.aio.live.connect(model=self.model, config=self.config) as session:
                # Send text message
                await session.send_client_content(
                    turns={"role": "user", "parts": [{"text": text}]}, 
                    turn_complete=True
                )
                
                # Collect audio response (following notebook pattern)
                output_file = "response.wav"
                with wave.open(output_file, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit  
                    wf.setframerate(24000)  # Gemini outputs 24kHz
                    
                    turn = session.receive()
                    async for response in turn:
                        if response.data is not None:
                            wf.writeframes(response.data)
                            print('.', end='')
                
                print(f"\n✅ Audio saved as {output_file}")
                return output_file
                
        except Exception as e:
            print(f"❌ Text-to-speech error: {e}")
            return None

async def main():
    API_KEY = "AIzaSyC9_QNT5xBMh3s8BySrI7EAqu6DgdFYDLM"
    
    ai = SimpleAudioAI(API_KEY)
    
    print("🚀 Simple Audio AI Started!")
    print("Make sure Pi audio stream is running\n")
    
    try:
        while True:
            print("\n" + "="*40)
            
            # Step 1: Get audio from Pi
            audio_data = ai.capture_audio_from_pi(duration=3)
            if not audio_data:
                await asyncio.sleep(2)
                continue
            
            # Step 2: Send to Gemini (audio -> text)
            response_text = await ai.send_audio_to_gemini(audio_data)
            if not response_text:
                continue
            
            # Step 3: Convert response to speech (text -> audio)
            audio_file = await ai.text_to_speech_gemini(response_text)
            if audio_file:
                print(f"🎵 Play {audio_file} to hear the response!")
            
            # Wait before next cycle
            await asyncio.sleep(3)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped")

if __name__ == "__main__":
    asyncio.run(main())