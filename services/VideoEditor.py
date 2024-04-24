from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def cut_video_file(filename: str, start_time: int, end_time: int):
    ffmpeg_extract_subclip(filename, start_time, end_time, targetname=filename.replace(".mp4", "") + "_cropped.mp4")
