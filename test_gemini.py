"""
Simple test to verify Gemini LIVE API connection works
"""
import asyncio
from google import genai

async def test_gemini_connection():
    # Replace with your actual API key
    API_KEY = "AIzaSyC9_QNT5xBMh3s8BySrI7EAqu6DgdFYDLM"
    
    client = genai.Client(api_key=API_KEY)
    model = "gemini-live-2.5-flash-preview"  # This model supports text output
    
    config = {
        "response_modalities": ["TEXT"],  # Start with text to test connection
        "system_instruction": "You are a helpful assistant. Keep responses short."
    }
    
    try:
        print("Testing Gemini LIVE API connection...")
        
        async with client.aio.live.connect(model=model, config=config) as session:
            # Send a simple text message
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": "Hello! Say hi back in one sentence."}]}, 
                turn_complete=True
            )
            
            # Get response
            async for response in session.receive():
                if response.text is not None:
                    print(f"✅ Gemini responded: {response.text}")
                    return True
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_gemini_connection())