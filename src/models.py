import uuid
from uuid import UUID
from dataclasses import dataclass

from conf.config import BASE_DIR, settings

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


class FileError(Exception):
    pass


class File:
    def __init__(self,
                 name: str,
                 text: str | None = None,
                 path: str | None = None,
                 user_id: int = None):
        self.name = name
        self.path = path or str(STORAGE_DIR / name)
        self.user_id = user_id or None
        self.text = text

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


# @dataclass
# class Role:
#     name: str


@dataclass
class Tag:
    name: str


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