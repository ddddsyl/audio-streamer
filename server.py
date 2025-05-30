from flask import Flask, render_template_string
from flask_socketio import SocketIO
import numpy as np
import wave
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Remove ssl_context

# Audio config
FORMAT = 2  # pyaudio.paInt16 equivalent
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORDINGS_DIR = "recordings"

os.makedirs(RECORDINGS_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <body>
            <button onclick="startStream()">Start Streaming</button>
            <button onclick="stopStream()">Stop</button>
            <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
            <script>
                const socket = io();
                let mediaStream;
                
                async function startStream() {
                    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const audioContext = new AudioContext();
                    const source = audioContext.createMediaStreamSource(mediaStream);
                    const processor = audioContext.createScriptProcessor(1024, 1, 1);
                    
                    source.connect(processor);
                    processor.connect(audioContext.destination);
                    
                    processor.onaudioprocess = (e) => {
                        const audioData = e.inputBuffer.getChannelData(0);
                        socket.emit('audio_stream', Array.from(audioData));
                    };
                }
                
                function stopStream() {
                    if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
                }
            </script>
        </body>
        </html>
    ''')

@socketio.on('audio_stream')
def handle_audio(data):
    filename = f"{RECORDINGS_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_array = np.array(data, dtype=np.float32)
    scaled = np.int16(audio_array * 32767)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(scaled.tobytes())

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  # Railway uses dynamic ports