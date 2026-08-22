import pyaudio
import wave
import os
from openai import OpenAI

class VoiceSTT:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()

    def record_audio(self, duration=5, filename="temp_input.wav"):
        """Graba audio del micrófono."""
        stream = self.audio.open(format=self.format, channels=self.channels,
                                rate=self.rate, input=True,
                                frames_per_buffer=self.chunk)

        print("🎙️ Escuchando...")
        frames = []
        for _ in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        print("✅ Grabación finalizada.")
        stream.stop_stream()
        stream.close()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return filename

    def transcribe(self, filename):
        """Transcribe el audio usando Whisper."""
        with open(filename, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text

if __name__ == "__main__":
    # Prueba rápida
    stt = VoiceSTT()
    # file = stt.record_audio(duration=3)
    # print(f"Transcripción: {stt.transcribe(file)}")
