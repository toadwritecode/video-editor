import os
import uuid
import moviepy.video.fx.all as vfx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import yt_dlp as youtube_dl
from pydantic import BaseModel, Field

from conf.config import settings
from schemas.actions_schema import VideoEditing


class YouTubeDlOptions(BaseModel):
    format: str = 'bestaudio/best'  # choice of quality
    extract_audio: bool = Field(default=False, alias='extractaudio')  # only keep the audio
    audio_format: str = Field(default="mp3", alias='audioformat')  # convert to mp3
    out_tmpl: str = Field(default=f'/src/{settings.STORAGE_NAME}/%(title)s.%(ext)s', alias='outtmpl')  # name the file the ID of the video
    no_play_list: bool = Field(default=True, alias='noplaylist')  # only download single song, not playlist
    list_formats: bool = Field(default=False, alias='listformats')  # print a list of the formats to stdout and exit


def _cut_video_file(path: str, start_time: int, end_time: int, new_file_name: str):
    cropped_video_path = path.replace(".mp4", f"_{new_file_name}.mp4")
    ffmpeg_extract_subclip(path, start_time, end_time, targetname=cropped_video_path)
    return cropped_video_path


def _merge_video_files(paths: list[str]):
    loaded_video_list = []
    merged_video_name = f"{paths[0].split('_')[0]}_modified_merged.mp4"
    for path in paths:
        loaded_video_list.append(VideoFileClip(path))

    final_clip = concatenate_videoclips(loaded_video_list)

    final_clip.write_videofile(merged_video_name)
    return merged_video_name.split('\\')[-1]


def _apply_video_speed_effect(path: str, speed: float):
    video = VideoFileClip(path)
    speed_modified_video_name = f"{path.split('.')[0]}_modified.mp4"
    final_clip = video.fx(vfx.speedx, speed)
    final_clip.write_videofile(speed_modified_video_name)
    return speed_modified_video_name.split('\\')[-1]


def edit_video(editing: VideoEditing, path: str) -> str | None:
    frame_paths = []
    edited_video_path = None
    for frame in editing.frames:
        frame_id = str(uuid.uuid4())
        frame_path = _cut_video_file(path, frame.cut_from, frame.cut_to, frame_id)
        if frame.speed:
            frame_path = _apply_video_speed_effect(path, frame.speed)
        frame_paths.extend([frame_path] * frame.times)

    if frame_paths:
        edited_video_path = _merge_video_files(frame_paths)

    if editing.speed:
        edited_video_path = _apply_video_speed_effect(path, editing.speed)

    # # remove used frames
    for path in set(frame_paths):
        os.remove(path)

    return edited_video_path


def extract_audio_from_video_file(path: str) -> str:
    audio_clip = AudioFileClip(path)
    path = path.replace(".mp4", "_audio.wav")
    audio_clip.write_audiofile(path)
    file_name = path.split("\\")[-1]
    return file_name


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
    path_win = file_name.split('\\')
    path = file_name.split('/')
    path: list[str] = path if len(path) > 1 else path_win
    return path[-1]
