import json

import speech_recognition as sr
recognizer = sr.Recognizer()

RECOGNIZE_CHUNK_DURATION = 1


def generate_audio_chunks(path: str, chunk_duration: int):
    with sr.AudioFile(path) as source:
        audio_duration = source.DURATION
        chunk_size = int(audio_duration / chunk_duration)

        for i in range(chunk_size):
            start = i * chunk_duration
            end = min((i + 1) * chunk_duration, audio_duration)
            audio = recognizer.record(source, duration=end-start, offset=start)
            yield audio


def transcribe_audio(path: str) -> str:
    results = []

    for audio in generate_audio_chunks(path, RECOGNIZE_CHUNK_DURATION):
        text = recognizer.recognize_vosk(audio, language="ru")
        results.append(json.loads(text)['text'])

    transcribed_text = " ".join(results)
    return transcribed_text
