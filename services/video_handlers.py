import json
import os
import uuid

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import speech_recognition as sr
import yt_dlp as youtube_dl
from pydantic import BaseModel, Field

from schemas.actions_schema import VideoEditing

recognizer = sr.Recognizer()


class YouTubeDlOptions(BaseModel):
    format: str = 'bestaudio/best'  # choice of quality
    extract_audio: bool = Field(default=False, alias='extractaudio')  # only keep the audio
    audio_format: str = Field(default="mp3", alias='audioformat')  # convert to mp3
    out_tmpl: str = Field(default='/video/%(title)s.%(ext)s', alias='outtmpl')  # name the file the ID of the video
    no_play_list: bool = Field(default=True, alias='noplaylist')  # only download single song, not playlist
    list_formats: bool = Field(default=False, alias='listformats')  # print a list of the formats to stdout and exit


def _cut_video_file(path: str, start_time: int, end_time: int, new_file_name: str):
    cropped_video_path = path.replace(".mp4", f"_{new_file_name}.mp4")
    ffmpeg_extract_subclip(path, start_time, end_time, targetname=cropped_video_path)
    return cropped_video_path


def _merge_video_files(paths: list[str]):
    loaded_video_list = []
    merged_video_name = f"{paths[0].split('_')[0]}_merged.mp4"
    for video in paths:
        loaded_video_list.append(VideoFileClip(video))

    final_clip = concatenate_videoclips(loaded_video_list)

    final_clip.write_videofile(merged_video_name)
    return merged_video_name


def edit_video(editing: VideoEditing, path: str):
    frame_paths = []
    for frame in editing.frames:
        piece_id = str(uuid.uuid4())
        frame_path = _cut_video_file(path, frame.cut_from, frame.cut_to, piece_id)
        frame_paths.append(frame_path)

    merged_video_name = _merge_video_files(frame_paths)

    # remove used frames
    [os.remove(path) for path in frame_paths]

    return merged_video_name


def transcribe_audio(path: str) -> str:
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)

    text = recognizer.recognize_vosk(audio, language="ru")

    return json.loads(text)


def extract_audio_from_video_file(path: str) -> str:
    audio_clip = AudioFileClip(path)
    path = path.replace(".mp4", "_audio.wav")
    audio_clip.write_audiofile(path)
    return path


def get_youtube_video_info(link: str, options: YouTubeDlOptions, download: bool = False):
    with youtube_dl.YoutubeDL(options.dict(by_alias=True)) as ydl:
        data = ydl.extract_info(link, download=download)
    return data


def get_youtube_video_formats(link: str):
    data = get_youtube_video_info(link=link, options=YouTubeDlOptions())
    return data.get('formats', [data])


def download_youtube_video(link: str, options: YouTubeDlOptions):
    data = get_youtube_video_info(link=link, options=options, download=True)
    file_name = data.get("requested_downloads", [])[0].get("filename")
    path: list[str] = file_name.split('\\')
    return path[1] if len(path) > 1 else path
