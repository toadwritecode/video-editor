import json

import speech_recognition as sr
recognizer = sr.Recognizer()

RECOGNIZE_CHUNK_DURATION = 1


def transcribe_audio(path: str) -> str:
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)

    text = recognizer.recognize_vosk(audio, language="ru")

    return json.loads(text)['text']