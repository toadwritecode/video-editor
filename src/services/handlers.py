from fastapi import UploadFile

import models
import queries.queries
from conf.config import settings, BASE_DIR
from repository import Repository
from schemas.actions_schema import VideoEditing
from utils.video import download_youtube_video, YouTubeDlOptions, extract_audio_from_video_file, edit_video

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


def save_user_file(repo: Repository, username: str, file: UploadFile):
    filename = file.filename
    file_path = STORAGE_DIR / filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    with repo:
        user = repo.get(username)
        file = models.File(name=filename)
        user.append_file(file)

        repo.add(user)
        repo.commit()

    return filename


def save_user_file_from_youtube(link: str, options: YouTubeDlOptions, username: str):
    # Пока для тасок из очереди зашиваем внутрь функции завсимость репозитория
    repo = Repository()
    filename = download_youtube_video(link, options)

    file = models.File(name=filename)
    try:
        with repo:
            user = repo.get(username)
            user.append_file(file)
            repo.add(user)
            repo.commit()

        return filename
    except models.FileError:
        pass


def extract_user_audio_from_video_file(username: str, filename: str):
    repository = Repository()

    user_file_path = queries.queries.get_path_user_file(repository, username, filename)

    if not user_file_path:
        return

    filename = extract_audio_from_video_file(user_file_path)

    file = models.File(filename)
    try:
        with repository:
            user = repository.get(username)
            user.append_file(file)
            repository.add(user)
            repository.commit()

        return filename
    except models.FileError:
        pass


def edit_user_video(editing: VideoEditing, username, filename):
    repository = Repository()
    user_file_path = queries.queries.get_path_user_file(repository, username, filename)

    if not user_file_path:
        return

    filename = edit_video(editing, user_file_path)

    file = models.File(filename)
    try:
        with repository:
            user = repository.get(username)
            user.append_file(file)
            repository.add(user)
            repository.commit()

        return filename
    except models.FileError:
        pass