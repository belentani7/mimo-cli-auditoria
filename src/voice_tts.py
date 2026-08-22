import os
import io
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import pygame

class VoiceTTS:
    def __init__(self, api_key=None, provider="openai"):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.provider = provider
        pygame.mixer.init()

    def speak(self, text, voice="alloy"):
        """Genera voz y la reproduce directamente sin archivos MP3 externos visibles."""
        if self.provider == "openai":
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            # Usar buffer en memoria para evitar archivos MP3 en el disco del usuario
            byte_stream = io.BytesIO(response.content)
            audio = AudioSegment.from_file(byte_stream, format="mp3")
            play(audio)

        elif self.provider == "elevenlabs":
            # Nota: ElevenLabs requiere su propia API Key y librería
            # Por ahora usamos OpenAI como default de alta calidad
            pass

if __name__ == "__main__":
    # Prueba rápida
    tts = VoiceTTS()
    # tts.speak("Hola, soy Mimo. Estoy listo para ayudarte.")
