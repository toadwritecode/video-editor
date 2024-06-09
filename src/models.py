import uuid
from uuid import UUID
from dataclasses import dataclass

from conf.config import BASE_DIR, settings

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


class FileError(Exception):
    pass


@dataclass
class SingingMistake:
    name: str


class File:
    def __init__(self,
                 name: str,
                 text: str | None = None,
                 path: str | None = None,
                 user_id: int = None,
                 singing_mistakes: list[SingingMistake] | None = None,
                 high_notes_deviation_score: int | None = None,
                 low_notes_deviation_score: int | None = None,
                 timing_deviation_score: int | None = None
                 ):
        self.name = name
        self.path = path or str(STORAGE_DIR / name)
        self.user_id = user_id or None
        self.text = text
        self.tags = singing_mistakes or list()
        self.high_notes_deviation_score = high_notes_deviation_score
        self.low_notes_deviation_score = low_notes_deviation_score
        self.timing_deviation_score = timing_deviation_score

    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return other.name == self.name

    def __hash__(self):
        return hash(self.name)


class RefreshToken:
    def __init__(self,
                 user_id: UUID,
                 refresh_token: str):
        self.refresh_token = refresh_token
        self.user_id = user_id


class User:
    def __init__(self, password: str,
                 username: str,
                 role: str,
                 email: str | None = None,
                 full_name: str | None = None,
                 files: list[File] | None = None
                 ):
        self.hashed_password = password
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role
        self.uuid = str(uuid.uuid4())
        self.files = files or list()

    def append_file(self, file: File):
        if file in self.files:
            raise FileError('This file already exists')
        self.files.append(file)

    def get_vocal_recommendation(self):
        if not self.files:
            return None
        count_files = len(self.files)

        avg_high_notes_deviation_score = round(sum([file.high_notes_deviation_score
                                                    for file in self.files]) / count_files, 2)
        avg_low_notes_deviation_score = round(sum([file.low_notes_deviation_score
                                                   for file in self.files]) / count_files, 2)
        avg_timing_deviation_score = round(sum([file.timing_deviation_score
                                                for file in self.files]) / count_files, 2)


