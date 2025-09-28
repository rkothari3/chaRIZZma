Get started with Live API

Note: Introducing a new version of the Gemini 2.5 Flash Live model, with improved function calling and conversational accuracy
The Live API enables low-latency, real-time voice and video interactions with Gemini. It processes continuous streams of audio, video, or text to deliver immediate, human-like spoken responses, creating a natural conversational experience for your users.

Live API Overview

Live API offers a comprehensive set of features such as Voice Activity Detection, tool use and function calling, session management (for managing long running conversations) and ephemeral tokens (for secure client-sided authentication).

This page gets you up and running with examples and basic code samples.

Try the Live API in Google AI Studiomic

Example applications
Check out the following example applications that illustrate how to use Live API for end-to-end use cases:

Live audio starter app on AI Studio, using JavaScript libraries to connect to Live API and stream bidirectional audio through your microphone and speakers.
Live API Python cookbook using Pyaudio that connects to Live API.
Partner integrations
If you prefer a simpler development process, you can use Daily, LiveKit or Voximplant. These are third-party partner platforms that have already integrated the Gemini Live API over the WebRTC protocol to streamline the development of real-time audio and video applications.

Before you begin building
There are two important decisions to make before you begin building with the Live API: choosing a model and choosing an implementation approach.

Choose an audio generation architecture
If you're building an audio-based use case, your choice of model determines the audio generation architecture used to create the audio response:

Native audio: This option provides the most natural and realistic-sounding speech and better multilingual performance. It also enables advanced features like affective (emotion-aware) dialogue, proactive audio (where the model can decide to ignore or respond to certain inputs), and "thinking". Native audio is supported by the following native audio models:
NEW: gemini-2.5-flash-native-audio-preview-09-2025
gemini-2.5-flash-preview-native-audio-dialog
gemini-2.5-flash-exp-native-audio-thinking-dialog
Half-cascade audio: This option uses a cascaded model architecture (native audio input and text-to-speech output). It offers better performance and reliability in production environments, especially with tool use. Half-cascaded audio is supported by the following models:
gemini-live-2.5-flash-preview
gemini-2.0-flash-live-001
Choose an implementation approach
When integrating with Live API, you'll need to choose one of the following implementation approaches:

Server-to-server: Your backend connects to the Live API using WebSockets. Typically, your client sends stream data (audio, video, text) to your server, which then forwards it to the Live API.
Client-to-server: Your frontend code connects directly to the Live API using WebSockets to stream data, bypassing your backend.
Note: Client-to-server generally offers better performance for streaming audio and video, since it bypasses the need to send the stream to your backend first. It's also easier to set up since you don't need to implement a proxy that sends data from your client to your server and then your server to the API. However, for production environments, in order to mitigate security risks, we recommend using ephemeral tokens instead of standard API keys.
Get started
This example reads a WAV file, sends it in the correct format, and saves the received data as WAV file.

You can send audio by converting it to 16-bit PCM, 16kHz, mono format, and you can receive audio by setting AUDIO as response modality. The output uses a sample rate of 24kHz.

Python
JavaScript

# Test file: https://storage.googleapis.com/generativeai-downloads/data/16000.wav
# Install helpers for converting files: pip install librosa soundfile
import asyncio
import io
from pathlib import Path
import wave
from google import genai
from google.genai import types
import soundfile as sf
import librosa

client = genai.Client()

# New native audio model:
model = "gemini-2.5-flash-native-audio-preview-09-2025"

config = {
  "response_modalities": ["AUDIO"],
  "system_instruction": "You are a helpful assistant and answer in a friendly tone.",
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:

        buffer = io.BytesIO()
        y, sr = librosa.load("sample.wav", sr=16000)
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()

        # If already in correct format, you can use this:
        # audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)  # Output is 24kHz

        async for response in session.receive():
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())

/////////////////////////////////////////////////////////////////////

Live API capabilities guide

Preview: The Live API is in preview.
This is a comprehensive guide that covers capabilities and configurations available with the Live API. See Get started with Live API page for a overview and sample code for common use cases.

Before you begin
Familiarize yourself with core concepts: If you haven't already done so, read the Get started with Live API page first. This will introduce you to the fundamental principles of the Live API, how it works, and the distinction between the different models and their corresponding audio generation methods (native audio or half-cascade).
Try the Live API in AI Studio: You may find it useful to try the Live API in Google AI Studio before you start building. To use the Live API in Google AI Studio, select Stream.
Establishing a connection
The following example shows how to create a connection with an API key:

Python
JavaScript

import asyncio
from google import genai

client = genai.Client()

model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        print("Session started")

if __name__ == "__main__":
    asyncio.run(main())
Note: You can only set one modality in the response_modalities field. This means that you can configure the model to respond with either text or audio, but not both in the same session.
Interaction modalities
The following sections provide examples and supporting context for the different input and output modalities available in Live API.

Sending and receiving text
Here's how you can send and receive text:

Python
JavaScript

import asyncio
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello, how are you?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.text is not None:
                print(response.text, end="")

if __name__ == "__main__":
    asyncio.run(main())
Incremental content updates
Use incremental updates to send text input, establish session context, or restore session context. For short contexts you can send turn-by-turn interactions to represent the exact sequence of events:

Python
JavaScript

turns = [
    {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
    {"role": "model", "parts": [{"text": "Paris"}]},
]

await session.send_client_content(turns=turns, turn_complete=False)

turns = [{"role": "user", "parts": [{"text": "What is the capital of Germany?"}]}]

await session.send_client_content(turns=turns, turn_complete=True)
For longer contexts it's recommended to provide a single message summary to free up the context window for subsequent interactions. See Session Resumption for another method for loading session context.

Sending and receiving audio
The most common audio example, audio-to-audio, is covered in the Getting started guide.

Here's an audio-to-text example that reads a WAV file, sends it in the correct format and receives text output:

Python
JavaScript

# Test file: https://storage.googleapis.com/generativeai-downloads/data/16000.wav
# Install helpers for converting files: pip install librosa soundfile
import asyncio
import io
from pathlib import Path
from google import genai
from google.genai import types
import soundfile as sf
import librosa

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:

        buffer = io.BytesIO()
        y, sr = librosa.load("sample.wav", sr=16000)
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()

        # If already in correct format, you can use this:
        # audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
And here is a text-to-audio example. You can receive audio by setting AUDIO as response modality. This example saves the received data as WAV file:

Python
JavaScript

import asyncio
import wave
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["AUDIO"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        message = "Hello how are you?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())
Audio formats
Audio data in the Live API is always raw, little-endian, 16-bit PCM. Audio output always uses a sample rate of 24kHz. Input audio is natively 16kHz, but the Live API will resample if needed so any sample rate can be sent. To convey the sample rate of input audio, set the MIME type of each audio-containing Blob to a value like audio/pcm;rate=16000.

Audio transcriptions
You can enable transcription of the model's audio output by sending output_audio_transcription in the setup config. The transcription language is inferred from the model's response.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["AUDIO"],
        "output_audio_transcription": {}
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello? Gemini are you there?"

        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for response in session.receive():
            if response.server_content.model_turn:
                print("Model turn:", response.server_content.model_turn)
            if response.server_content.output_transcription:
                print("Transcript:", response.server_content.output_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())
You can enable transcription of the audio input by sending input_audio_transcription in setup config.

Python
JavaScript

import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {
    "response_modalities": ["TEXT"],
    "input_audio_transcription": {},
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_data = Path("16000.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type='audio/pcm;rate=16000')
        )

        async for msg in session.receive():
            if msg.server_content.input_transcription:
                print('Transcript:', msg.server_content.input_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())
Stream audio and video
To see an example of how to use the Live API in a streaming audio and video format, run the "Live API - Get Started" file in the cookbooks repository:

View on Colab

Change voice and language
The Live API models each support a different set of voices. Half-cascade supports Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr. Native audio supports a much longer list (identical to the TTS model list). You can listen to all the voices in AI Studio.

To specify a voice, set the voice name within the speechConfig object as part of the session configuration:

Python
JavaScript

config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}
    },
}
Note: If you're using the generateContent API, the set of available voices is slightly different. See the audio generation guide for generateContent audio generation voices.
The Live API supports multiple languages.

To change the language, set the language code within the speechConfig object as part of the session configuration:

Python
JavaScript

config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "language_code": "de-DE"
    }
}
Note: Native audio output models automatically choose the appropriate language and don't support explicitly setting the language code.
Native audio capabilities
The following capabilities are only available with native audio. You can learn more about native audio in Choose a model and audio generation.

Note: Native audio models currently have limited tool use support. See Overview of supported tools for details.
How to use native audio output
To use native audio output, configure one of the native audio models and set response_modalities to AUDIO.

See Send and receive audio for a full example.

Python
JavaScript

model = "gemini-2.5-flash-native-audio-preview-09-2025"
config = types.LiveConnectConfig(response_modalities=["AUDIO"])

async with client.aio.live.connect(model=model, config=config) as session:
    # Send audio input and receive audio
Affective dialog
This feature lets Gemini adapt its response style to the input expression and tone.

To use affective dialog, set the api version to v1alpha and set enable_affective_dialog to truein the setup message:

Python
JavaScript

client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    enable_affective_dialog=True
)
Note that affective dialog is currently only supported by the native audio output models.

Proactive audio
When this feature is enabled, Gemini can proactively decide not to respond if the content is not relevant.

To use it, set the api version to v1alpha and configure the proactivity field in the setup message and set proactive_audio to true:

Python
JavaScript

client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    proactivity={'proactive_audio': True}
)
Note that proactive audio is currently only supported by the native audio output models.

Native audio output with thinking
Native audio output supports thinking capabilities, available via a separate model gemini-2.5-flash-exp-native-audio-thinking-dialog.

See Send and receive audio for a full example.

Python
JavaScript

model = "gemini-2.5-flash-exp-native-audio-thinking-dialog"
config = types.LiveConnectConfig(response_modalities=["AUDIO"])

async with client.aio.live.connect(model=model, config=config) as session:
    # Send audio input and receive audio
Voice Activity Detection (VAD)
Voice Activity Detection (VAD) allows the model to recognize when a person is speaking. This is essential for creating natural conversations, as it allows a user to interrupt the model at any time.

When VAD detects an interruption, the ongoing generation is canceled and discarded. Only the information already sent to the client is retained in the session history. The server then sends a BidiGenerateContentServerContent message to report the interruption.

The Gemini server then discards any pending function calls and sends a BidiGenerateContentServerContent message with the IDs of the canceled calls.

Python
JavaScript

async for response in session.receive():
    if response.server_content.interrupted is True:
        # The generation was interrupted

        # If realtime playback is implemented in your application,
        # you should stop playing audio and clear queued playback here.
Automatic VAD
By default, the model automatically performs VAD on a continuous audio input stream. VAD can be configured with the realtimeInputConfig.automaticActivityDetection field of the setup configuration.

When the audio stream is paused for more than a second (for example, because the user switched off the microphone), an audioStreamEnd event should be sent to flush any cached audio. The client can resume sending audio data at any time.

Python
JavaScript

# example audio file to try:
# URL = "https://storage.googleapis.com/generativeai-downloads/data/hello_are_you_there.pcm"
# !wget -q $URL -O sample.pcm
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        # if stream gets paused, send:
        # await session.send_realtime_input(audio_stream_end=True)

        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
With send_realtime_input, the API will respond to audio automatically based on VAD. While send_client_content adds messages to the model context in order, send_realtime_input is optimized for responsiveness at the expense of deterministic ordering.

Automatic VAD configuration
For more control over the VAD activity, you can configure the following parameters. See API reference for more info.

Python
JavaScript

from google.genai import types

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False, # default
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 100,
        }
    }
}
Disable automatic VAD
Alternatively, the automatic VAD can be disabled by setting realtimeInputConfig.automaticActivityDetection.disabled to true in the setup message. In this configuration the client is responsible for detecting user speech and sending activityStart and activityEnd messages at the appropriate times. An audioStreamEnd isn't sent in this configuration. Instead, any interruption of the stream is marked by an activityEnd message.

Python
JavaScript

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
}

async with client.aio.live.connect(model=model, config=config) as session:
    # ...
    await session.send_realtime_input(activity_start=types.ActivityStart())
    await session.send_realtime_input(
        audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
    )
    await session.send_realtime_input(activity_end=types.ActivityEnd())
    # ...
Token count
You can find the total number of consumed tokens in the usageMetadata field of the returned server message.

Python
JavaScript

async for message in session.receive():
    # The server will periodically send messages that include UsageMetadata.
    if message.usage_metadata:
        usage = message.usage_metadata
        print(
            f"Used {usage.total_token_count} tokens in total. Response token breakdown:"
        )
        for detail in usage.response_tokens_details:
            match detail:
                case types.ModalityTokenCount(modality=modality, token_count=count):
                    print(f"{modality}: {count}")
Media resolution
You can specify the media resolution for the input media by setting the mediaResolution field as part of the session configuration:

Python
JavaScript

from google.genai import types

config = {
    "response_modalities": ["AUDIO"],
    "media_resolution": types.MediaResolution.MEDIA_RESOLUTION_LOW,
}
Limitations
Consider the following limitations of the Live API when you plan your project.

Response modalities
You can only set one response modality (TEXT or AUDIO) per session in the session configuration. Setting both results in a config error message. This means that you can configure the model to respond with either text or audio, but not both in the same session.

Client authentication
The Live API only provides server-to-server authentication by default. If you're implementing your Live API application using a client-to-server approach, you need to use ephemeral tokens to mitigate security risks.

Session duration
Audio-only sessions are limited to 15 minutes, and audio plus video sessions are limited to 2 minutes. However, you can configure different session management techniques for unlimited extensions on session duration.

Context window
A session has a context window limit of:

128k tokens for native audio output models
32k tokens for other Live API models
Supported languages
Live API supports the following languages.

Note: Native audio output models automatically choose the appropriate language and don't support explicitly setting the language code.
Language	BCP-47 Code	Language	BCP-47 Code
German (Germany)	de-DE	English (Australia)*	en-AU
English (UK)*	en-GB	English (India)	en-IN
English (US)	en-US	Spanish (US)	es-US
French (France)	fr-FR	Hindi (India)	hi-IN
Portuguese (Brazil)	pt-BR	Arabic (Generic)	ar-XA
Spanish (Spain)*	es-ES	French (Canada)*	fr-CA
Indonesian (Indonesia)	id-ID	Italian (Italy)	it-IT
Japanese (Japan)	ja-JP	Turkish (Turkey)	tr-TR
Vietnamese (Vietnam)	vi-VN	Bengali (India)	bn-IN
Gujarati (India)*	gu-IN	Kannada (India)*	kn-IN
Marathi (India)	mr-IN	Malayalam (India)*	ml-IN
Tamil (India)	ta-IN	Telugu (India)	te-IN
Dutch (Netherlands)	nl-NL	Korean (South Korea)	ko-KR
Mandarin Chinese (China)*	cmn-CN	Polish (Poland)	pl-PL
Russian (Russia)	ru-RU	Thai (Thailand)	th-TH
Languages marked with an asterisk (*) are not available for Native audio.



//////////////////////////////////////////////////////////////////////

ool use with Live API

Tool use allows Live API to go beyond just conversation by enabling it to perform actions in the real-world and pull in external context while maintaining a real time connection. You can define tools such as Function calling, Code execution, and Google Search with the Live API.

Overview of supported tools
Here's a brief overview of the available tools for each model:

Tool	
gemini-live-2.5-flash-preview
gemini-2.0-flash-live-001
gemini-2.5-flash-native-audio-preview-09-2025
gemini-2.5-flash-preview-native-audio-dialog
gemini-2.5-flash-exp-native-audio-thinking-dialog
Search	Yes	Yes	Yes
Function calling	Yes	Yes	No
Code execution	Yes	No	No
URL context	Yes	No	No
Function calling
Live API supports function calling, just like regular content generation requests. Function calling lets the Live API interact with external data and programs, greatly increasing what your applications can accomplish.

You can define function declarations as part of the session configuration. After receiving tool calls, the client should respond with a list of FunctionResponse objects using the session.send_tool_response method.

See the Function calling tutorial to learn more.

Note: Unlike the generateContent API, the Live API doesn't support automatic tool response handling. You must handle tool responses manually in your client code.
Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

# Simple function definitions
turn_on_the_lights = {"name": "turn_on_the_lights"}
turn_off_the_lights = {"name": "turn_off_the_lights"}

tools = [{"function_declarations": [turn_on_the_lights, turn_off_the_lights]}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Turn on the lights please"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)
            elif chunk.tool_call:
                function_responses = []
                for fc in chunk.tool_call.function_calls:
                    function_response = types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={ "result": "ok" } # simple, hard-coded function response
                    )
                    function_responses.append(function_response)

                await session.send_tool_response(function_responses=function_responses)

if __name__ == "__main__":
    asyncio.run(main())
From a single prompt, the model can generate multiple function calls and the code necessary to chain their outputs. This code executes in a sandbox environment, generating subsequent BidiGenerateContentToolCall messages.

Asynchronous function calling
Note: Asynchronous function calling is only supported in half-cascade audio generation.
Function calling executes sequentially by default, meaning execution pauses until the results of each function call are available. This ensures sequential processing, which means you won't be able to continue interacting with the model while the functions are being run.

If you don't want to block the conversation, you can tell the model to run the functions asynchronously. To do so, you first need to add a behavior to the function definitions:

Python
JavaScript

  # Non-blocking function definitions
  turn_on_the_lights = {"name": "turn_on_the_lights", "behavior": "NON_BLOCKING"} # turn_on_the_lights will run asynchronously
  turn_off_the_lights = {"name": "turn_off_the_lights"} # turn_off_the_lights will still pause all interactions with the model
NON-BLOCKING ensures the function runs asynchronously while you can continue interacting with the model.

Then you need to tell the model how to behave when it receives the FunctionResponse using the scheduling parameter. It can either:

Interrupt what it's doing and tell you about the response it got right away (scheduling="INTERRUPT"),
Wait until it's finished with what it's currently doing (scheduling="WHEN_IDLE"),
Or do nothing and use that knowledge later on in the discussion (scheduling="SILENT")

Python
JavaScript

# for a non-blocking function definition, apply scheduling in the function response:
  function_response = types.FunctionResponse(
      id=fc.id,
      name=fc.name,
      response={
          "result": "ok",
          "scheduling": "INTERRUPT" # Can also be WHEN_IDLE or SILENT
      }
  )
Code execution
You can define code execution as part of the session configuration. This lets the Live API generate and execute Python code and dynamically perform computations to benefit your results. See the Code execution tutorial to learn more.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'code_execution': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "Compute the largest prime palindrome under 100000."
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)

                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                      if part.executable_code is not None:
                        print(part.executable_code.code)

                      if part.code_execution_result is not None:
                        print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
Grounding with Google Search
You can enable Grounding with Google Search as part of the session configuration. This increases the Live API's accuracy and prevents hallucinations. See the Grounding tutorial to learn more.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

tools = [{'google_search': {}}]
config = {"response_modalities": ["TEXT"], "tools": tools}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        prompt = "When did the last Brazil vs. Argentina soccer match happen?"
        await session.send_client_content(turns={"parts": [{"text": prompt}]})

        async for chunk in session.receive():
            if chunk.server_content:
                if chunk.text is not None:
                    print(chunk.text)

                # The model might generate and execute Python code to use Search
                model_turn = chunk.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                      if part.executable_code is not None:
                        print(part.executable_code.code)

                      if part.code_execution_result is not None:
                        print(part.code_execution_result.output)

if __name__ == "__main__":
    asyncio.run(main())
Combining multiple tools
You can combine multiple tools within the Live API, increasing your application's capabilities even more:

Python
JavaScript

prompt = """
Hey, I need you to do three things for me.

1. Compute the largest prime palindrome under 100000.
2. Then use Google Search to look up information about the largest earthquake in California the week of Dec 5 2024?
3. Turn on the lights

Thanks!
"""

tools = [
    {"google_search": {}},
    {"code_execution": {}},
    {"function_declarations": [turn_on_the_lights, turn_off_the_lights]},
]

config = {"response_modalities": ["TEXT"], "tools": tools}

# ... remaining model call


///////////////////////////////////////////////////////////////////////

Session management with Live API

In the Live API, a session refers to a persistent connection where input and output are streamed continuously over the same connection (read more about how it works). This unique session design enables low latency and supports unique features, but can also introduce challenges, like session time limits, and early termination. This guide covers strategies for overcoming the session management challenges that can arise when using the Live API.

Session lifetime
Without compression, audio-only sessions are limited to 15 minutes, and audio-video sessions are limited to 2 minutes. Exceeding these limits will terminate the session (and therefore, the connection), but you can use context window compression to extend sessions to an unlimited amount of time.

The lifetime of a connection is limited as well, to around 10 minutes. When the connection terminates, the session terminates as well. In this case, you can configure a single session to stay active over multiple connections using session resumption. You'll also receive a GoAway message before the connection ends, allowing you to take further actions.

Context window compression
To enable longer sessions, and avoid abrupt connection termination, you can enable context window compression by setting the contextWindowCompression field as part of the session configuration.

In the ContextWindowCompressionConfig, you can configure a sliding-window mechanism and the number of tokens that triggers compression.

Python
JavaScript

from google.genai import types

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    context_window_compression=(
        # Configures compression with default parameters.
        types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        )
    ),
)
Session resumption
To prevent session termination when the server periodically resets the WebSocket connection, configure the sessionResumption field within the setup configuration.

Passing this configuration causes the server to send SessionResumptionUpdate messages, which can be used to resume the session by passing the last resumption token as the SessionResumptionConfig.handle of the subsequent connection.

Resumption tokens are valid for 2 hr after the last sessions termination.

Python
JavaScript

import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"

async def main():
    print(f"Connecting to the service with handle {previous_session_handle}...")
    async with client.aio.live.connect(
        model=model,
        config=types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            session_resumption=types.SessionResumptionConfig(
                # The handle of the session to resume is passed here,
                # or else None to start a new session.
                handle=previous_session_handle
            ),
        ),
    ) as session:
        while True:
            await session.send_client_content(
                turns=types.Content(
                    role="user", parts=[types.Part(text="Hello world!")]
                )
            )
            async for message in session.receive():
                # Periodically, the server will send update messages that may
                # contain a handle for the current state of the session.
                if message.session_resumption_update:
                    update = message.session_resumption_update
                    if update.resumable and update.new_handle:
                        # The handle should be retained and linked to the session.
                        return update.new_handle

                # For the purposes of this example, placeholder input is continually fed
                # to the model. In non-sample code, the model inputs would come from
                # the user.
                if message.server_content and message.server_content.turn_complete:
                    break

if __name__ == "__main__":
    asyncio.run(main())
Receiving a message before the session disconnects
The server sends a GoAway message that signals that the current connection will soon be terminated. This message includes the timeLeft, indicating the remaining time and lets you take further action before the connection will be terminated as ABORTED.

Python
JavaScript

async for response in session.receive():
    if response.go_away is not None:
        # The connection will soon be terminated
        print(response.go_away.time_left)
Receiving a message when the generation is complete
The server sends a generationComplete message that signals that the model finished generating the response.

Python
JavaScript

async for response in session.receive():
    if response.server_content.generation_complete is True:
        # The generation is complete


Ephemeral tokens

Ephemeral tokens are short-lived authentication tokens for accessing the Gemini API through WebSockets. They are designed to enhance security when you are connecting directly from a user's device to the API (a client-to-server implementation). Like standard API keys, ephemeral tokens can be extracted from client-side applications such as web browsers or mobile apps. But because ephemeral tokens expire quickly and can be restricted, they significantly reduce the security risks in a production environment.

Note: Ephemeral tokens are only compatible with Live API at this time. You should use them when accessing the Live API directly from client-side applications to enhance API key security.
How ephemeral tokens work
Here's how ephemeral tokens work at a high level:

Your client (e.g. web app) authenticates with your backend.
Your backend requests an ephemeral token from Gemini API's provisioning service.
Gemini API issues a short-lived token.
Your backend sends the token to the client for WebSocket connections to Live API. You can do this by swapping your API key with an ephemeral token.
The client then uses the token as if it were an API key.
Ephemeral tokens overview

This enhances security because even if extracted, the token is short-lived, unlike a long-lived API key deployed client-side. Since the client sends data directly to Gemini, this also improves latency and avoids your backends needing to proxy the real time data.

Create an ephemeral token
Here is a simplified example of how to get an ephemeral token from Gemini. By default, you'll have 1 minute to start new Live API sessions using the token from this request (newSessionExpireTime), and 30 minutes to send messages over that connection (expireTime).

Python
JavaScript

import datetime

now = datetime.datetime.now(tz=datetime.timezone.utc)

client = genai.Client(
    http_options={'api_version': 'v1alpha',}
)

token = client.auth_tokens.create(
    config = {
    'uses': 1, # The ephemeral token can only be used to start a single session
    'expire_time': now + datetime.timedelta(minutes=30), # Default is 30 minutes in the future
    # 'expire_time': '2025-05-17T00:00:00Z',   # Accepts isoformat.
    'new_session_expire_time': now + datetime.timedelta(minutes=1), # Default 1 minute in the future
    'http_options': {'api_version': 'v1alpha'},
  }
)

# You'll need to pass the value under token.name back to your client to use it
For expireTime value constraints, defaults, and other field specs, see the API reference. Within the expireTime timeframe, you'll need sessionResumption to reconnect the call every 10 minutes (this can be done with the same token even if uses: 1).

It's also possible to lock an ephemeral token to a set of configurations. This might be useful to further improve security of your application and keep your system instructions on the server side.

Python
JavaScript

client = genai.Client(
    http_options={'api_version': 'v1alpha',}
)

token = client.auth_tokens.create(
    config = {
    'uses': 1,
    'live_connect_constraints': {
        'model': 'gemini-2.0-flash-live-001',
        'config': {
            'session_resumption':{},
            'temperature':0.7,
            'response_modalities':['TEXT']
        }
    },
    'http_options': {'api_version': 'v1alpha'},
    }
)

# You'll need to pass the value under token.name back to your client to use it
You can also lock a subset of fields, see the SDK documentation for more info.

Connect to Live API with an ephemeral token
Once you have an ephemeral token, you use it as if it were an API key (but remember, it only works for the live API, and only with the v1alpha version of the API).

Note that use of ephemeral tokens only adds value when deploying applications that follow client-to-server implementation approach.

JavaScript

import { GoogleGenAI, Modality } from '@google/genai';

// Use the token generated in the "Create an ephemeral token" section here
const ai = new GoogleGenAI({
  apiKey: token.name
});
const model = 'gemini-2.0-flash-live-001';
const config = { responseModalities: [Modality.TEXT] };

async function main() {

  const session = await ai.live.connect({
    model: model,
    config: config,
    callbacks: { ... },
  });

  // Send content...

  session.close();
}

main();
Note: If not using the SDK, note that ephemeral tokens must either be passed in an access_token query parameter, or in an HTTP Authorization prefixed by the auth-scheme Token.
See Get started with Live API for more examples.

Best practices
Set a short expiration duration using the expire_time parameter.
Tokens expire, requiring re-initiation of the provisioning process.
Verify secure authentication for your own backend. Ephemeral tokens will only be as secure as your backend authentication method.
Generally, avoid using ephemeral tokens for backend-to-Gemini connections, as this path is typically considered secure.

////////////////////////////////////////////////////////////////////////

Prompt design strategies

Prompt design is the process of creating prompts, or natural language requests, that elicit accurate, high quality responses from a language model.

This page introduces basic concepts, strategies, and best practices to get you started designing prompts to get the most out of Gemini AI models.

Topic-specific prompt guides
Looking for more specific prompt strategies? Check out our other prompting guides on:

Prompting with media files
Prompting for image generation with Imagen and Gemini Native Image Generation
Prompting for video generation
You can find other sample prompts in the prompt gallery meant to interactively showcase many of the concepts shared in this guide.

Clear and specific instructions
An effective and efficient way to customize model behavior is to provide it with clear and specific instructions. Instructions can be in the form of a question, step-by-step tasks, or as complex as mapping out a user's experience and mindset.

Input
Input is the required text in the prompt that you want the model to provide a response to. Inputs can be a question that the model answers (question input), a task the model performs (task input), an entity the model operates on (entity input), or partial input that the model completes or continues (completion input).

Input type	Prompt	Generated output
Question	

What's a good name for a flower shop that specializes in selling bouquets of
dried flowers? Create a list of 5 options with just the names.

Here are 10 names for a flower shop specializing in dried flowers:

1. Everlasting Blooms
2. Dried & Delightful
3. The Petal Preserve
4. Whispers of Wildflowers
5. Forever Blooms
Task	
Give me a simple list of just the things that I must bring on a camping trip. The list should have 5 items.
1. **Tent:** Your shelter from the elements.
2. **Sleeping Bag:** Stay warm and comfortable.
3. **Sleeping Pad:** Insulation and cushioning for a good night's sleep.
4. **Headlamp or Flashlight:** Light for nighttime activities.
5. **First Aid Kit:** Be prepared for minor injuries.
Entity	

Classify the following items as [large, small]:
Elephant
Mouse
Snail

Here's the classification:

* **Elephant:** Large
* **Mouse:** Small
* **Snail:** Small
Partial input completion
Generative language models work like an advanced auto completion tool. When you provide partial content, the model can provide the rest of the content or what it thinks is a continuation of that content as a response. When doing so, if you include any examples or context, the model can take those examples or context into account.

The following example provides a prompt with an instruction and an entity input:

Prompt:
For the given order, return a JSON object that has the fields cheeseburger, hamburger, fries, or
drink, with the value being the quantity.

Order: A burger and a drink.
Response:
{
"cheeseburger": 0,
"hamburger": 1,
"fries": 0,
"drink": 1
}
(gemini-2.5-flash)
While the model did as prompted, writing out the instructions in natural language can sometimes be challenging and it leaves a lot to the model's interpretation. For example, a restaurants menu might contain many items. To reduce the size of the JSON response, you probably want to omit the items that weren't ordered. In this case, you can give an example and a response prefix and let the model complete it:

Prompt:
Valid fields are cheeseburger, hamburger, fries, and drink.
Order: Give me a cheeseburger and fries
Output:
```
{
"cheeseburger": 1,
"fries": 1
}
```
Order: I want two burgers, a drink, and fries.
Output:
Response:
```
{
"hamburger": 2,
"drink": 1,
"fries": 1
}
```
(gemini-2.5-flash)
Notice how "cheeseburger" was excluded from the output because it wasn't a part of the order.

Constraints
Specify any constraints on reading the prompt or generating a response. You can tell the model what to do and not to do. For example, you can specify a constraint in the prompt on how long you want a summary to be:

Prompt:

Summarize this text in one sentence:
Text: A quantum computer exploits quantum mechanical phenomena to perform calculations exponentially
faster than any modern traditional computer. At very tiny scales, physical matter acts as both
particles and as waves, and quantum computing uses specialized hardware to leverage this behavior.
The operating principles of quantum devices is beyond the scope of classical physics. When deployed
at scale, quantum computers could be used in a wide variety of applications such as: in
cybersecurity to break existing encryption methods while helping researchers create new ones, in
meteorology to develop better weather forecasting etc. However, the current state of the art quantum
computers are still largely experimental and impractical.
Response:

Exploiting quantum mechanical phenomena, quantum computers can perform calculations exponentially faster than traditional computers for potential applications like cybersecurity and meteorology, although they are currently largely experimental and impractical.
(gemini-2.5-flash)
Response format
You can give instructions that specify the format of the response. For example, you can ask for the response to be formatted as a table, bulleted list, elevator pitch, keywords, sentence, or paragraph. The following system instruction tells the model to be more conversational in its response:

System instruction
All questions should be answered comprehensively with details, unless the user requests a concise response specifically.
Prompt
What is a smart way to make a business that sells DVD's in 2025?
Response:
Starting a business selling DVDs in 2025 presents significant challenges due to the overwhelming dominance of digital streaming and on-demand services; a "smart" approach would therefore require a highly specialized niche, a strong value proposition beyond just the disc, and likely a focus on community or collector markets rather than mainstream consumption.

Here's a breakdown of what a smart DVD business in 2025 would likely entail:

1. Extreme Niche Specialization: You cannot compete with streaming libraries. Your business must focus on what digital doesn't offer easily or at all. This could include:

* Out-of-Print & Rare Titles: Sourcing films or TV shows that have never been released digitally or are currently unavailable on major streaming platforms.
....
(gemini-2.5-flash)
Format responses with the completion strategy
The completion strategy can also help format the response. The following example prompts the model to create an essay outline:

Prompt:
Create an outline for an essay about hummingbirds.
Response:
Here is a possible outline for an essay about hummingbirds:

I. Introduction
A. Hook: Start with a captivating fact or description about hummingbirds (e.g., their speed, iridescent colors, or tiny size).
B. Background: Briefly introduce hummingbirds – where they are found (Americas), their reputation as unique birds.
C. Thesis Statement: State the main point of the essay, which could be about the remarkable adaptations, behaviors, and ecological importance of hummingbirds.

II. Appearance and Identification
.....
(gemini-2.5-flash)
The prompt didn't specify the format for the outline and the model chose a format for you. To get the model to return an outline in a specific format, you can add text that represents the start of the outline and let the model complete it based on the pattern that you initiated.

Prompt:
Create an outline for an essay about hummingbirds.
I. Introduction
*
Response:
Okay, here is an outline for an essay about hummingbirds, starting from the introduction you provided:

I. Introduction
* Hook: Start with a captivating fact or description about hummingbirds (e.g., their speed, iridescent colors, or tiny size).
* Background: Briefly introduce hummingbirds – where they are found (Americas), their reputation as unique birds, and their general characteristics.
* Thesis Statement: State the main point of the essay, focusing on the remarkable adaptations, behaviors, and ecological significance that make hummingbirds extraordinary.
.....
(gemini-2.5-flash)
Zero-shot vs few-shot prompts
You can include examples in the prompt that show the model what getting it right looks like. The model attempts to identify patterns and relationships from the examples and applies them when generating a response. Prompts that contain a few examples are called few-shot prompts, while prompts that provide no examples are called zero-shot prompts. Few-shot prompts are often used to regulate the formatting, phrasing, scoping, or general patterning of model responses. Use specific and varied examples to help the model narrow its focus and generate more accurate results.

We recommend to always include few-shot examples in your prompts. Prompts without few-shot examples are likely to be less effective. In fact, you can remove instructions from your prompt if your examples are clear enough in showing the task at hand.

The following zero-shot prompt asks the model to choose the best explanation.

Prompt:
Please choose the best explanation to the question:

Question: How is snow formed?
Explanation1: Snow is formed when water vapor in the air freezes into ice
crystals in the atmosphere, which can combine and grow into snowflakes as they
fall through the atmosphere and accumulate on the ground.
Explanation2: Water vapor freezes into ice crystals forming snow.
Answer:
Response:
Explanation1 is the better explanation because it provides more detail on the
process, including how ice crystals combine and grow into snowflakes as they
fall through the atmosphere.
(gemini-2.5-flash)
If your use case requires the model to produce concise responses, you can include examples in the prompt that give preference to concise responses.

The following prompt provides two examples that show preference to the shorter explanations. In the response, you can see that the examples guided the model to choose the shorter explanation (Explanation2) as opposed to the longer explanation (Explanation1) like it did previously.

Prompt:
Below are some examples showing a question, explanation, and answer format:

Question: Why is the sky blue?
Explanation1: The sky appears blue because of Rayleigh scattering, which causes
shorter blue wavelengths of light to be scattered more easily than longer red
wavelengths, making the sky look blue.
Explanation2: Due to Rayleigh scattering effect.
Answer: Explanation2

Question: What is the cause of earthquakes?
Explanation1: Sudden release of energy in the Earth's crust.
Explanation2: Earthquakes happen when tectonic plates suddenly slip or break
apart, causing a release of energy that creates seismic waves that can shake the
ground and cause damage.
Answer: Explanation1

Now, Answer the following question given the example formats above:

Question: How is snow formed?
Explanation1: Snow is formed when water vapor in the air freezes into ice
crystals in the atmosphere, which can combine and grow into snowflakes as they
fall through the atmosphere and accumulate on the ground.
Explanation2: Water vapor freezes into ice crystals forming snow.
Answer:
Response:
Answer: Explanation2
(gemini-2.5-flash)
Optimal number of examples
Models like Gemini can often pick up on patterns using a few examples, though you may need to experiment with the number of examples to provide in the prompt for the best results. At the same time, if you include too many examples, the model may start to overfit the response to the examples.

Patterns vs anti patterns
Using examples to show the model a pattern to follow is more effective than using examples to show the model an anti pattern to avoid.

⛔ Negative pattern:

Example
Don't end haikus with a question:
Haiku are fun
A short and simple poem
Don't you enjoy them?

✅ Positive pattern:

Example
Always end haikus with an assertion:
Haiku are fun
A short and simple poem
A joy to write

Consistent formatting
Make sure that the structure and formatting of few-shot examples are the same to avoid responses with undesired formats. One of the primary objectives of adding few-shot examples in prompts is to show the model the response format. Therefore, it is essential to ensure a consistent format across all examples, especially paying attention to XML tags, white spaces, newlines, and example splitters.

Add context
You can include instructions and information in a prompt that the model needs to solve a problem, instead of assuming that the model has all of the required information. This contextual information helps the model understand the constraints and details of what you're asking for it to do.

The following example asks the model to give troubleshooting guidance for a router:

Prompt:
What should I do to fix my disconnected wifi? The light on my Google
Wifi router is yellow and blinking slowly.
Response:
A yellow blinking light on your Google Wifi router usually indicates a problem
with the internet connection. Here are some steps to troubleshoot and fix the
issue:
1. Restart your router and modem:
- Unplug your modem from the power outlet and wait for 30 seconds.
- Plug your modem back in and wait for it to fully boot up.
- Unplug your Google Wifi router and wait for 30 seconds.
- Plug your Google Wifi router back in and wait for it to fully boot up.
.....
(gemini-2.5-flash)
The response looks like generic troubleshooting information that's not specific to the router or the status of the LED indicator lights.

To customize the response for the specific router, you can add to the prompt the router's troubleshooting guide as context for it to refer to when providing a response.

Prompt:
Answer the question using the text below. Respond with only the text provided.
Question: What should I do to fix my disconnected wifi? The light on my Google Wifi router is yellow and blinking slowly.

Text:
Color: Slowly pulsing yellow
What it means: There is a network error.
What to do:
Check that the Ethernet cable is connected to both your router and your modem and both devices are turned on. You might need to unplug and plug in each device again.

Color: Fast blinking yellow
What it means: You are holding down the reset button and are factory resetting this device.
What to do:
If you keep holding down the reset button, after about 12 seconds, the light will turn solid yellow. Once it is solid yellow, let go of the factory reset button.

Color: Solid yellow
What it means: Router is factory resetting.
What to do:
This can take up to 10 minutes. When it's done, the device will reset itself and start pulsing white, letting you know it's ready for setup.

Color: Solid red
What it means: Something is wrong.
What to do:
Critical failure. Factory reset the router. If the light stays red, contact Wifi customer support.
Response:
Check that the Ethernet cable is connected to both your router and your modem and both devices are turned on. You might need to unplug and plug in each device again.
(gemini-2.5-flash)
Add prefixes
A prefix is a word or phrase that you add to the prompt content that can serve several purposes, depending on where you put the prefix:

Input prefix: Adding a prefix to the input signals semantically meaningful parts of the input to the model. For example, the prefixes "English:" and "French:" demarcate two different languages.
Output prefix: Even though the output is generated by the model, you can add a prefix for the output in the prompt. The output prefix gives the model information about what's expected as a response. For example, the output prefix "JSON:" signals to the model that the output should be in JSON format.
Example prefix: In few-shot prompts, adding prefixes to the examples provides labels that the model can use when generating the output, which makes it easier to parse output content.
In the following example, "Text:" is the input prefix and "The answer is:" is the output prefix.

Prompt:
Classify the text as one of the following categories.
- large
- small
Text: Rhino
The answer is: large
Text: Mouse
The answer is: small
Text: Snail
The answer is: small
Text: Elephant
The answer is:
Response:
The answer is: large
(gemini-2.5-flash)
Break down prompts into components
For use cases that require complex prompts, you can help the model manage this complexity by breaking things down into simpler components.

Break down instructions: Instead of having many instructions in one prompt, create one prompt per instruction. You can choose which prompt to process based on the user's input.

Chain prompts: For complex tasks that involve multiple sequential steps, make each step a prompt and chain the prompts together in a sequence. In this sequential chain of prompts, the output of one prompt in the sequence becomes the input of the next prompt. The output of the last prompt in the sequence is the final output.

Aggregate responses: Aggregation is when you want to perform different parallel tasks on different portions of the data and aggregate the results to produce the final output. For example, you can tell the model to perform one operation on the first part of the data, perform another operation on the rest of the data and aggregate the results.

Experiment with model parameters
Each call that you send to a model includes parameter values that control how the model generates a response. The model can generate different results for different parameter values. Experiment with different parameter values to get the best values for the task. The parameters available for different models may differ. The most common parameters are the following:

Max output tokens: Specifies the maximum number of tokens that can be generated in the response. A token is approximately four characters. 100 tokens correspond to roughly 60-80 words.

Temperature: The temperature controls the degree of randomness in token selection. The temperature is used for sampling during response generation, which occurs when topP and topK are applied. Lower temperatures are good for prompts that require a more deterministic or less open-ended response, while higher temperatures can lead to more diverse or creative results. A temperature of 0 is deterministic, meaning that the highest probability response is always selected.

topK: The topK parameter changes how the model selects tokens for output. A topK of 1 means the selected token is the most probable among all the tokens in the model's vocabulary (also called greedy decoding), while a topK of 3 means that the next token is selected from among the 3 most probable using the temperature. For each token selection step, the topK tokens with the highest probabilities are sampled. Tokens are then further filtered based on topP with the final token selected using temperature sampling.

topP: The topP parameter changes how the model selects tokens for output. Tokens are selected from the most to least probable until the sum of their probabilities equals the topP value. For example, if tokens A, B, and C have a probability of 0.3, 0.2, and 0.1 and the topP value is 0.5, then the model will select either A or B as the next token by using the temperature and exclude C as a candidate. The default topP value is 0.95.

stop_sequences: Set a stop sequence to tell the model to stop generating content. A stop sequence can be any sequence of characters. Try to avoid using a sequence of characters that may appear in the generated content.

Prompt iteration strategies
Prompt design can sometimes require a few iterations before you consistently get the response you're looking for. This section provides guidance on some things you can try when iterating on your prompts:

Use different phrasing: Using different words or phrasing in your prompts often yields different responses from the model even though they all mean the same thing. If you're not getting the expected results from your prompt, try rephrasing it.

Version 1:
How do I bake a pie?

Version 2:
Suggest a recipe for a pie.

Version 3:
What's a good pie recipe?

Switch to an analogous task: If you can't get the model to follow your instructions for a task, try giving it instructions for an analogous task that achieves the same result.

This prompt tells the model to categorize a book by using predefined categories:

Prompt:
Which category does The Odyssey belong to:
thriller
sci-fi
mythology
biography
Response:
The Odyssey belongs to the category of **mythology**.

Here's why:

* **Mythology:** The Odyssey tells the story of Odysseus, a hero from Greek mythology, and his
journey home after the Trojan War. It features gods, monsters, and supernatural events common to
Greek mythology.
.....
(gemini-2.5-flash)
The response is correct, but the model didn't stay within the bounds of the options. You also want to model to just respond with one of the options instead of in a full sentence. In this case, you can rephrase the instructions as a multiple choice question and ask the model to choose an option.

Prompt:
Multiple choice problem: Which of the following options describes the book The Odyssey?
Options:



thriller

sci-fi

mythology

biography
Response:
The correct answer is mythology.
(gemini-2.5-flash)
Change the order of prompt content: The order of the content in the prompt can sometimes affect the response. Try changing the content order and see how that affects the response.


Version 1:
[examples]
[context]
[input]

Version 2:
[input]
[examples]
[context]

Version 3:
[examples]
[input]
[context]
Fallback responses
A fallback response is a response returned by the model when either the prompt or the response triggers a safety filter. An example of a fallback response is "I'm not able to help with that, as I'm only a language model."

If the model responds with a fallback response, try increasing the temperature.

Things to avoid
Avoid relying on models to generate factual information.
Use with care on math and logic problems.
Generative models under the hood
This section aims to answer the question - Is there randomness in generative models' responses, or are they deterministic?

The short answer - yes to both. When you prompt a generative model, a text response is generated in two stages. In the first stage, the generative model processes the input prompt and generates a probability distribution over possible tokens (words) that are likely to come next. For example, if you prompt with the input text "The dog jumped over the ... ", the generative model will produce an array of probable next words:


[("fence", 0.77), ("ledge", 0.12), ("blanket", 0.03), ...]
This process is deterministic; a generative model will produce this same distribution every time it's input the same prompt text.

In the second stage, the generative model converts these distributions into actual text responses through one of several decoding strategies. A simple decoding strategy might select the most likely token at every timestep. This process would always be deterministic. However, you could instead choose to generate a response by randomly sampling over the distribution returned by the model. This process would be stochastic (random). Control the degree of randomness allowed in this decoding process by setting the temperature. A temperature of 0 means only the most likely tokens are selected, and there's no randomness. Conversely, a high temperature injects a high degree of randomness into the tokens selected by the model, leading to more unexpected, surprising model responses.



/////////////////////////////////////////////////////////////////////////////////

Video understanding

Gemini models can process videos, enabling many frontier developer use cases that would have historically required domain specific models. Some of Gemini's vision capabilities include the ability to:

Describe, segment, and extract information from videos
Answer questions about video content
Refer to specific timestamps within a video
Gemini was built to be multimodal from the ground up and we continue to push the frontier of what is possible. This guide shows how to use the Gemini API to generate text responses based on video inputs.

Video input
You can provide videos as input to Gemini in the following ways:

Upload a video file using the File API before making a request to generateContent. Use this method for files larger than 20MB, videos longer than approximately 1 minute, or when you want to reuse the file across multiple requests.
Pass inline video data with the request to generateContent. Use this method for smaller files (<20MB) and shorter durations.
Pass YouTube URLs as part of your generateContent request.
Upload a video file
You can use the Files API to upload a video file. Always use the Files API when the total request size (including the file, text prompt, system instructions, etc.) is larger than 20 MB, the video duration is significant, or if you intend to use the same video in multiple prompts. The File API accepts video file formats directly.

The following code downloads the sample video, uploads it using the File API, waits for it to be processed, and then uses the file reference in a generateContent request.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

myfile = client.files.upload(file="path/to/sample.mp4")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=[myfile, "Summarize this video. Then create a quiz with an answer key based on the information in this video."]
)

print(response.text)
To learn more about working with media files, see Files API.

Pass video data inline
Instead of uploading a video file using the File API, you can pass smaller videos directly in the request to generateContent. This is suitable for shorter videos under 20MB total request size.

Here's an example of providing inline video data:

Python
JavaScript
REST

from google import genai
from google.genai import types

# Only for videos of size <20Mb
video_file_name = "/path/to/your/video.mp4"
video_bytes = open(video_file_name, 'rb').read()

client = genai.Client()
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
            ),
            types.Part(text='Please summarize the video in 3 sentences.')
        ]
    )
)
Pass YouTube URLs
Preview: The YouTube URL feature is in preview and is available at no charge. Pricing and rate limits are likely to change.
You can pass YouTube URLs directly to Gemini API as part of your generateContentrequest as follows:

Python
JavaScript
Go
REST

response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                file_data=types.FileData(file_uri='https://www.youtube.com/watch?v=9hE5-98ZeCg')
            ),
            types.Part(text='Please summarize the video in 3 sentences.')
        ]
    )
)
Limitations:

For the free tier, you can't upload more than 8 hours of YouTube video per day.
For the paid tier, there is no limit based on video length.
For models prior to Gemini 2.5, you can upload only 1 video per request. For Gemini 2.5 and later models, you can upload a maximum of 10 videos per request.
You can only upload public videos (not private or unlisted videos).
Refer to timestamps in the content
You can ask questions about specific points in time within the video using timestamps of the form MM:SS.

Python
JavaScript
Go
REST

prompt = "What are the examples given at 00:05 and 00:10 supposed to show us?" # Adjusted timestamps for the NASA video
Transcribe video and provide visual descriptions
The Gemini models can transcribe and provide visual descriptions of video content by processing both the audio track and visual frames. For visual descriptions, the model samples the video at a rate of 1 frame per second. This sampling rate may affect the level of detail in the descriptions, particularly for videos with rapidly changing visuals.

Python
JavaScript
Go
REST

prompt = "Transcribe the audio from this video, giving timestamps for salient events in the video. Also provide visual descriptions."
Customize video processing
You can customize video processing in the Gemini API by setting clipping intervals or providing custom frame rate sampling.

Tip: Video clipping and frames per second (FPS) are supported by all models, but the quality is significantly higher from 2.5 series models.
Set clipping intervals
You can clip video by specifying videoMetadata with start and end offsets.

Python

from google import genai
from google.genai import types

client = genai.Client()
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                file_data=types.FileData(file_uri='https://www.youtube.com/watch?v=XEzRZ35urlk'),
                video_metadata=types.VideoMetadata(
                    start_offset='1250s',
                    end_offset='1570s'
                )
            ),
            types.Part(text='Please summarize the video in 3 sentences.')
        ]
    )
)
Set a custom frame rate
You can set custom frame rate sampling by passing an fps argument to videoMetadata.

Note: Due to built-in per image based safety checks, the same video may get blocked at some fps and not at others due to different extracted frames.
Python

from google import genai
from google.genai import types

# Only for videos of size <20Mb
video_file_name = "/path/to/your/video.mp4"
video_bytes = open(video_file_name, 'rb').read()

client = genai.Client()
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=video_bytes,
                    mime_type='video/mp4'),
                video_metadata=types.VideoMetadata(fps=5)
            ),
            types.Part(text='Please summarize the video in 3 sentences.')
        ]
    )
)
By default 1 frame per second (FPS) is sampled from the video. You might want to set low FPS (< 1) for long videos. This is especially useful for mostly static videos (e.g. lectures). If you want to capture more details in rapidly changing visuals, consider setting a higher FPS value.

Supported video formats
Gemini supports the following video format MIME types:

video/mp4
video/mpeg
video/mov
video/avi
video/x-flv
video/mpg
video/webm
video/wmv
video/3gpp
Technical details about videos
Supported models & context: All Gemini 2.0 and 2.5 models can process video data.
Models with a 2M context window can process videos up to 2 hours long at default media resolution or 6 hours long at low media resolution, while models with a 1M context window can process videos up to 1 hour long at default media resolution or 3 hours long at low media resolution.
File API processing: When using the File API, videos are stored at 1 frame per second (FPS) and audio is processed at 1Kbps (single channel). Timestamps are added every second.
These rates are subject to change in the future for improvements in inference.
You can override the 1 FPS sampling rate by setting a custom frame rate.
Token calculation: Each second of video is tokenized as follows:
Individual frames (sampled at 1 FPS):
If mediaResolution is set to low, frames are tokenized at 66 tokens per frame.
Otherwise, frames are tokenized at 258 tokens per frame.
Audio: 32 tokens per second.
Metadata is also included.
Total: Approximately 300 tokens per second of video at default media resolution, or 100 tokens per second of video at low media resolution.
Timestamp format: When referring to specific moments in a video within your prompt, use the MM:SS format (e.g., 01:15 for 1 minute and 15 seconds).
Best practices:
Use only one video per prompt request for optimal results.
If combining text and a single video, place the text prompt after the video part in the contents array.
Be aware that fast action sequences might lose detail due to the 1 FPS sampling rate. Consider slowing down such clips if necessary.
What's next
This guide shows how to upload video files and generate text outputs from video inputs. To learn more, see the following resources:

System instructions: System instructions let you steer the behavior of the model based on your specific needs and use cases.
Files API: Learn more about uploading and managing files for use with Gemini.
File prompting strategies: The Gemini API supports prompting with text, image, audio, and video data, also known as multimodal prompting.
Safety guidance: Sometimes generative AI models produce unexpected outputs, such as outputs that are inaccurate, biased, or offensive. Post-processing and human evaluation are essential to limit the risk of harm from such outputs.


/////////////////////////////////////////////////////////////////////////////////

udio understanding

Gemini can analyze and understand audio input, enabling use cases like the following:

Describe, summarize, or answer questions about audio content.
Provide a transcription of the audio.
Analyze specific segments of the audio.
This guide shows you how to use the Gemini API to generate a text response to audio input.

Before you begin
Before calling the Gemini API, ensure you have your SDK of choice installed, and a Gemini API key configured and ready to use.

Input audio
You can provide audio data to Gemini in the following ways:

Upload an audio file before making a request to generateContent.
Pass inline audio data with the request to generateContent.
Upload an audio file
You can use the Files API to upload an audio file. Always use the Files API when the total request size (including the files, text prompt, system instructions, etc.) is larger than 20 MB.

The following code uploads an audio file and then uses the file in a call to generateContent.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

myfile = client.files.upload(file="path/to/sample.mp3")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=["Describe this audio clip", myfile]
)

print(response.text)
To learn more about working with media files, see Files API.

Pass audio data inline
Instead of uploading an audio file, you can pass inline audio data in the request to generateContent:

Python
JavaScript
Go

from google import genai
from google.genai import types

with open('path/to/small-sample.mp3', 'rb') as f:
    audio_bytes = f.read()

client = genai.Client()
response = client.models.generate_content(
  model='gemini-2.5-flash',
  contents=[
    'Describe this audio clip',
    types.Part.from_bytes(
      data=audio_bytes,
      mime_type='audio/mp3',
    )
  ]
)

print(response.text)
A few things to keep in mind about inline audio data:

The maximum request size is 20 MB, which includes text prompts, system instructions, and files provided inline. If your file's size will make the total request size exceed 20 MB, then use the Files API to upload an audio file for use in the request.
If you're using an audio sample multiple times, it's more efficient to upload an audio file.
Get a transcript
To get a transcript of audio data, just ask for it in the prompt:

Python
JavaScript
Go

from google import genai

client = genai.Client()
myfile = client.files.upload(file='path/to/sample.mp3')
prompt = 'Generate a transcript of the speech.'

response = client.models.generate_content(
  model='gemini-2.5-flash',
  contents=[prompt, myfile]
)

print(response.text)
Refer to timestamps
You can refer to specific sections of an audio file using timestamps of the form MM:SS. For example, the following prompt requests a transcript that

Starts at 2 minutes 30 seconds from the beginning of the file.
Ends at 3 minutes 29 seconds from the beginning of the file.

Python
JavaScript
Go

# Create a prompt containing timestamps.
prompt = "Provide a transcript of the speech from 02:30 to 03:29."
Count tokens
Call the countTokens method to get a count of the number of tokens in an audio file. For example:

Python
JavaScript
Go

from google import genai

client = genai.Client()
response = client.models.count_tokens(
  model='gemini-2.5-flash',
  contents=[myfile]
)

print(response)
Supported audio formats
Gemini supports the following audio format MIME types:

WAV - audio/wav
MP3 - audio/mp3
AIFF - audio/aiff
AAC - audio/aac
OGG Vorbis - audio/ogg
FLAC - audio/flac
Technical details about audio
Gemini represents each second of audio as 32 tokens; for example, one minute of audio is represented as 1,920 tokens.
Gemini can "understand" non-speech components, such as birdsong or sirens.
The maximum supported length of audio data in a single prompt is 9.5 hours. Gemini doesn't limit the number of audio files in a single prompt; however, the total combined length of all audio files in a single prompt can't exceed 9.5 hours.
Gemini downsamples audio files to a 16 Kbps data resolution.
If the audio source contains multiple channels, Gemini combines those channels into a single channel.
What's next
This guide shows how to generate text in response to audio data. To learn more, see the following resources:

File prompting strategies: The Gemini API supports prompting with text, image, audio, and video data, also known as multimodal prompting.
System instructions: System instructions let you steer the behavior of the model based on your specific needs and use cases.
Safety guidance: Sometimes generative AI models produce unexpected outputs, such as outputs that are inaccur

Grounding with Google Search

Grounding with Google Search connects the Gemini model to real-time web content and works with all available languages. This allows Gemini to provide more accurate answers and cite verifiable sources beyond its knowledge cutoff.

Grounding helps you build applications that can:

Increase factual accuracy: Reduce model hallucinations by basing responses on real-world information.
Access real-time information: Answer questions about recent events and topics.
Provide citations: Build user trust by showing the sources for the model's claims.

Python
JavaScript
REST

from google import genai
from google.genai import types

client = genai.Client()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Who won the euro 2024?",
    config=config,
)

print(response.text)
You can learn more by trying the Search tool notebook.

How grounding with Google Search works
When you enable the google_search tool, the model handles the entire workflow of searching, processing, and citing information automatically.

grounding-overview

User Prompt: Your application sends a user's prompt to the Gemini API with the google_search tool enabled.
Prompt Analysis: The model analyzes the prompt and determines if a Google Search can improve the answer.
Google Search: If needed, the model automatically generates one or multiple search queries and executes them.
Search Results Processing: The model processes the search results, synthesizes the information, and formulates a response.
Grounded Response: The API returns a final, user-friendly response that is grounded in the search results. This response includes the model's text answer and groundingMetadata with the search queries, web results, and citations.
Understanding the Grounding Response
When a response is successfully grounded, the response includes a groundingMetadata field. This structured data is essential for verifying claims and building a rich citation experience in your application.


{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Spain won Euro 2024, defeating England 2-1 in the final. This victory marks Spain's record fourth European Championship title."
          }
        ],
        "role": "model"
      },
      "groundingMetadata": {
        "webSearchQueries": [
          "UEFA Euro 2024 winner",
          "who won euro 2024"
        ],
        "searchEntryPoint": {
          "renderedContent": "<!-- HTML and CSS for the search widget -->"
        },
        "groundingChunks": [
          {"web": {"uri": "https://vertexaisearch.cloud.google.com.....", "title": "aljazeera.com"}},
          {"web": {"uri": "https://vertexaisearch.cloud.google.com.....", "title": "uefa.com"}}
        ],
        "groundingSupports": [
          {
            "segment": {"startIndex": 0, "endIndex": 85, "text": "Spain won Euro 2024, defeatin..."},
            "groundingChunkIndices": [0]
          },
          {
            "segment": {"startIndex": 86, "endIndex": 210, "text": "This victory marks Spain's..."},
            "groundingChunkIndices": [0, 1]
          }
        ]
      }
    }
  ]
}
The Gemini API returns the following information with the groundingMetadata:

webSearchQueries : Array of the search queries used. This is useful for debugging and understanding the model's reasoning process.
searchEntryPoint : Contains the HTML and CSS to render the required Search Suggestions. Full usage requirements are detailed in the Terms of Service.
groundingChunks : Array of objects containing the web sources (uri and title).
groundingSupports : Array of chunks to connect model response text to the sources in groundingChunks. Each chunk links a text segment (defined by startIndex and endIndex) to one or more groundingChunkIndices. This is the key to building inline citations.
Grounding with Google Search can also be used in combination with the URL context tool to ground responses in both public web data and the specific URLs you provide.

Attributing Sources with inline Citations
The API returns structured citation data, giving you complete control over how you display sources in your user interface. You can use the groundingSupports and groundingChunks fields to link the model's statements directly to their sources. Here is a common pattern for processing the metadata to create a response with inline, clickable citations.

Python
JavaScript

def add_citations(response):
    text = response.text
    supports = response.candidates[0].grounding_metadata.grounding_supports
    chunks = response.candidates[0].grounding_metadata.grounding_chunks

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            # Create citation string like [1](link1)[2](link2)
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    citation_links.append(f"[{i + 1}]({uri})")

            citation_string = ", ".join(citation_links)
            text = text[:end_index] + citation_string + text[end_index:]

    return text

# Assuming response with grounding metadata
text_with_citations = add_citations(response)
print(text_with_citations)

Spain won Euro 2024, defeating England 2-1 in the final.[1](https:/...), [2](https:/...), [4](https:/...), [5](https:/...) This victory marks Spain's record-breaking fourth European Championship title.[5]((https:/...), [2](https:/...), [3](https:/...), [4](https:/...)
Pricing
When you use Grounding with Google Search, your project is billed per API request that includes the google_search tool. If the model decides to execute multiple search queries to answer a single prompt (for example, searching for "UEFA Euro 2024 winner" and "Spain vs England Euro 2024 final score" within the same API call), this counts as a single billable use of the tool for that request.

For detailed pricing information, see the Gemini API pricing page.

Supported Models
Experimental and Preview models are not included. You can find their capabilities on the model overview page.

Model	Grounding with Google Search
Gemini 2.5 Pro	✔️
Gemini 2.5 Flash	✔️
Gemini 2.5 Flash-Lite	✔️
Gemini 2.0 Flash	✔️
Gemini 1.5 Pro	✔️
Gemini 1.5 Flash	✔️
Note: Older models use a google_search_retrieval tool. For all current models, use the google_search tool as shown in the examples.
Grounding with Gemini 1.5 Models (Legacy)
While the google_search tool is recommended for Gemini 2.0 and later, Gemini 1.5 support a legacy tool named google_search_retrieval. This tool provides a dynamic mode that allows the model to decide whether to perform a search based on its confidence that the prompt requires fresh information. If the model's confidence is above a dynamic_threshold you set (a value between 0.0 and 1.0), it will perform a search.

Python
JavaScript
REST

# Note: This is a legacy approach for Gemini 1.5 models.
# The 'google_search' tool is recommended for all new development.
import os
from google import genai
from google.genai import types

client = genai.Client()

retrieval_tool = types.Tool(
    google_search_retrieval=types.GoogleSearchRetrieval(
        dynamic_retrieval_config=types.DynamicRetrievalConfig(
            mode=types.DynamicRetrievalConfigMode.MODE_DYNAMIC,
            dynamic_threshold=0.7 # Only search if confidence > 70%
        )
    )
)

config = types.GenerateContentConfig(
    tools=[retrieval_tool]
)

response = client.models.generate_content(
    model='gemini-1.5-flash',
    contents="Who won the euro 2024?",
    config=config,
)
print(response.text)
if not response.candidates[0].grounding_metadata:
  print("\nModel answered from its own knowledge.")
What's next
Try the Grounding with Google Search in the Gemini API Cookbook.
Learn about other available tools, like Function Calling.
Learn how to augment prompts with specific URLs using the URL context tool.