from flask import Flask, Response
import subprocess
import os
import signal

app = Flask(__name__)
current_process = None

@app.route('/audio_feed')
def audio_feed():
    global current_process

    def generate_audio():
        global current_process
        try:
            # Kill any existing process
            if current_process:
                current_process.terminate()

            # Start fresh arecord process
            current_process = subprocess.Popen([
                'arecord', '-D', 'hw:1,0', '-f', 'S16_LE', '-c', '1',
                '-r', '16000', '-t', 'wav', '--quiet', '-'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Send WAV header first
            wav_header = b'RIFF\xff\xff\xff\xffWAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\xff\xff\xff\xff'
            yield wav_header

            # Then stream audio data
            while current_process and current_process.poll() is None:
                audio_chunk = current_process.stdout.read(1024)
                if audio_chunk:
                    yield audio_chunk
                else:
                    break
        except Exception as e:
            print(f"Audio streaming error: {e}")

    return Response(generate_audio(), mimetype='audio/wav')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001)
    finally:
        if current_process:
            current_process.terminate()