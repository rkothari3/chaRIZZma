from flask import Flask, Response
import subprocess

app = Flask(__name__)

@app.route('/audio_feed')
def audio_feed():
    def generate_audio():
        try:
            # Use PulseAudio's parec instead of direct ALSA access
            audio_process = subprocess.Popen([
                'parec', '--format=s16le', '--rate=16000', '--channels=1'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Send basic WAV header
            wav_header = b'RIFF\xff\xff\xff\xffWAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\xff\xff\xff\xff'
            yield wav_header

            while audio_process.poll() is None:
                audio_chunk = audio_process.stdout.read(1024)
                if audio_chunk:
                    yield audio_chunk
                else:
                    break
        except Exception as e:
            print(f"Audio streaming error: {e}")

    return Response(generate_audio(), mimetype='audio/wav')

if __name__ == '__main__':
    print("Audio stream: http://143.215.189.141:5001/audio_feed")
    app.run(host='0.0.0.0', port=5001)