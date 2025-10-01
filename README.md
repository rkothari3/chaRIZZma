# chaRIZZma
## Inspiration
Ever freeze up when talking to someone you’re actually interested in? We wanted to create a tool that acts your pocket wingman…  helping you navigate conversations, break the ice, and drop smooth lines without looking awkward.

## What it does
chaRIZZma is an AI-powered wingman in hardware form. It uses a webcam and microphone to read facial expressions and catch the tone of conversations, then feeds that info into the Gemini API to generate real-time, context-aware “wingman advice.” Hit the button, and chaRIZZma whispers a smooth line into your Bluetooth earpiece, unlocking the secret to never being awkward and maxxing out your charisma :)

## How we built it
- **Hardware setup**: Raspberry Pi + webcam + microphone, streaming data to our computer over a local network.
- **Computer vision**: OpenCV to process facial expressions and sentiment.
- **Audio input**: Subprocess for capturing and analyzing voice data.
- **Processing**: Gemini API processes the combined data and spits out helpful, real-time conversational suggestions.
- **User flow**: A button triggers the response, and output is sent to a Bluetooth earpiece so you can stay low-key while your AI wingman does the heavy lifting.

Raspberry Pi captures video and audio → sends to local laptop

Laptop processes with OpenCV and Subprocess → prepares structured inputs

Gemini API generates suggestions → stores locally

Button press triggers retrieval → sends audio to audio output

## Challenges we ran into
- **Learning Raspberry Pi on the fly**: None of us had prior experience with Raspberry Pi development, so getting familiar with the ecosystem was a steep learning curve. Fortunately, we figured this out quickly and got a working pipeline running.
- **Real-time audio capture**: Initially, we struggled to capture audio continuously without an almost 20 second delay. After testing multiple approaches, we found Subprocess was the right tool to minimize the lag.
- **Balancing form factor and functionality**: We wanted chaRIZZma to feel sleek, not clunky. That meant cutting down on unnecessary components and making design decisions like choosing a webcam with a built-in mic, and carefully assembling everything into a compact, wearable form.
- **Audio + video integration**: Most libraries don’t handle both video and audio together smoothly. Our workaround was to capture them separately on their own servers and then re-sync the data when prompting the Gemini API.
- **Latency optimization**: The Raspberry Pi introduced noticeable lag, so we had to experiment with trade-offs in sampling rate and video quality to strike a balance between speed and accuracy.
- **System architecture**: Unlike a pure software project, this build required coordinating hardware inputs, AI outputs, and multiple pipelines. Designing a workflow that connected all the moving parts was a unique challenge for us.
- **Interaction design**: We needed a simple, reliable way to trigger Gemini responses, so we settled on a physical button for the prototype.
- **Prompt engineering**: Tuning Gemini to combine facial sentiment analysis with real-time conversation context without generating irrelevant or awkward output took lots of iteration.
- **Debugging hardware + AI**: This was the biggest hardware project any of us had worked on, so we learned the importance of modular testing. We had to validate each individual component before linking everything together into the final system.


## Accomplishments that we're proud of
- **Building a fully functional AI wingman**: Gives good advice that would actually be useful in a real conversation by effectively combining both facial sentiment and conversation flow to deliver lines that actually work. 
- **Executing under extreme time pressure**: We pulled an all-nighter and still completed our prototype on schedule, coordinating hardware, software, and AI systems. 
- **Seamless hardware-software integration**: From Raspberry Pi input to OpenCV analysis, PyAudio processing, Gemini API prompts, and Bluetooth output, we got multiple subsystems to work together reliably, with minimal lag and smooth real-time wingman support.
- **Designing a user-friendly system**: We simplified the setup to a compact form factor with minimal components and a single button trigger, making the prototype both functional and wearable, while keeping interactions natural and socially comfortable.

## What we learned
- **Crafting good conversation starters is an art**: Getting chaRIZZma to suggest lines that are smooth, context-aware, and socially appropriate is way harder than we expected, and AI has a sense of humor that sometimes won’t exactly match yours.
- **Simplicity is key in hardware projects**: Hardware adds complexity, so we learned that it’s best to focus on making each component work reliably first, then layer on extra features. Trying to do everything at once is a guaranteed recipe for chaos (and very stressed teammates).
- **Test everything before integration**: Making sure each individual component works on its own before connecting them was really important. 
- **Integrating AI into human interactions is tricky but powerful**: We learned how to combine sentiment analysis, conversation context, and AI reasoning to produce real-time advice that actually helps people feel more confident in social situations. It reinforced that AI can support humans without taking over the conversation.

## What's next for chaRIZZma

- **Miniaturizing the hardware**: We plan to make chaRIZZma more compact by designing a custom PCB, using a smaller camera, and integrating a smaller chip. The ultimate goal is for the system to be wearable as a discreet pendant, so your AI wingman can travel with you anywhere without being noticeable.
- **Refining prompt engineering**: We want to continue improving how Gemini interprets conversation and sentiment, making responses smarter, more context-aware, and more socially appropriate.
- **Expanding applications**: While we started with dating and casual conversations, we hope to eventually adapt chaRIZZma for interviews, public speaking, and other high-pressure scenarios where real-time conversational support can make a meaningful difference.

