import os
import uuid

from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker

import models
from conf.config import BASE_DIR, settings

from orm import start_mappers, engine

start_mappers()
default_session = sessionmaker(engine)

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


class Repository:
    def __init__(self, session=default_session):
        self.session_factory = session

    def __enter__(self):
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get(self, username: str) -> models.User | None:
        return (self.session.query(models.User)
                .filter(models.User.username == username)
                .first())

    def get_file_by_uuid(self, id: uuid.UUID) -> models.File | None:
        return (self.session.query(models.File)
                .filter(models.File.uuid == id)
                .first())

    def get_file_by_name(self, name: str) -> models.File | None:
        return (self.session.query(models.File)
                .filter(models.File.name == name)
                .first())

    def get_file_by_file_id_and_user_id(self,
                                        file_uuid: uuid.UUID,
                                        user_id: int) -> models.File | None:
        return (self.session.query(models.File)
                .filter(and_(
                    models.File.uuid == file_uuid,
                    models.File.user_id == user_id
                ))
                .first())

    def add(self, user: models.User):
        self.session.add(user)

    def add_file(self, file: models.File):
        self.session.add(file)

    def commit(self):
        self.session.commit()

    def get_user_available_files(self, username: str) -> list[dict]:
        user = self.get(username)
        files = user.files

        if not files:
            return []

        if os.path.exists(STORAGE_DIR):
            files = [{
                "name": file.name,
                "path": file.path,
                "text": file.extracted_text,
                "format": file.name.split('.')[-1]
            } for file in files]
            return files

    def delete_file(self, file: models.File):
        self.session.delete(file)

