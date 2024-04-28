import json

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import speech_recognition as sr

recognizer = sr.Recognizer()


def cut_video_file(path: str, start_time: int, end_time: int):
    cropped_video_path = path.replace(".mp4", "_cropped.mp4")
    ffmpeg_extract_subclip(path, start_time, end_time, targetname=cropped_video_path)
    return cropped_video_path


def transcribe_audio(path: str) -> str:
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)

    text = recognizer.recognize_vosk(audio, language="ru")

    return json.loads(text)


def extract_audio_from_video_file(path: str) -> str:
    audio_clip = AudioFileClip(path)
    path = path.replace(".mp4", "_audio.mp3")
    audio_clip.write_audiofile(path)
    return path