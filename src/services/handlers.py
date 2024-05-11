import uuid

from fastapi import UploadFile

import models
from conf.config import settings, BASE_DIR
from repository import Repository
from schemas.actions_schema import VideoEditing
from utils.video import download_youtube_video, YouTubeDlOptions, extract_audio_from_video_file, edit_video
from utils.audio import transcribe_audio


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


def extract_user_audio_from_video_file(
    user_id: int,
    file_uuid: uuid.UUID
):
    repo = Repository()

    with repo:
        file = repo.get_file_by_file_id_and_user_id(file_uuid, user_id)
        if not file:
            return

        extracted_audio_filename = extract_audio_from_video_file(file.path)

        file_for_save = models.File(extracted_audio_filename, None, user_id)
        try:
            with repo:
                repo.add_file(file_for_save)
                repo.commit()

            return extracted_audio_filename
        except models.FileError:
            pass


def edit_user_video(
    editing: VideoEditing,
    user_id: int,
    file_uuid: uuid.UUID
):
    repo = Repository()

    with repo:
        file = repo.get_file_by_file_id_and_user_id(file_uuid, user_id)
        if not file:
            return

        edited_filename = edit_video(editing, file.path)
        file_for_save = models.File(edited_filename, None, user_id)

        try:
            with repo:
                repo.add_file(file_for_save)
                repo.commit()

            return edited_filename
        except models.FileError:
            pass


def transcribe_text_from_audio_file(
    user_id: int,
    file_uuid: uuid.UUID
):
    repo = Repository()

    with repo:
        file = repo.get_file_by_file_id_and_user_id(file_uuid, user_id)
        if not file:
            return

        return transcribe_audio(file.path)


def get_file_by_uuid(repo: Repository, id: uuid.UUID):
    with repo:
        return repo.get_file_by_uuid(id)


def update_file_uuid_by_name(repo: Repository,
                             id: uuid.UUID,
                             name: str):
    with repo:
        file = repo.get_file_by_name(name)
        file.uuid = id
        repo.commit()

