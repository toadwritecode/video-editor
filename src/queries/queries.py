import os
from sqlalchemy.sql import text
from conf.config import BASE_DIR, settings
from repository import Repository

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


def get_user_available_files(repo: Repository, username: str) -> list[dict]:
    with repo:
        user = repo.get(username)
        files = user.files

    if not files:
        return []

    if os.path.exists(STORAGE_DIR):
        files = [{
            "name": file.name,
            "path": file.path,
            "format": file.name.split('.')[1]
        } for file in files]
        return files


def get_path_user_file(repo: Repository, username: str, filename: str) -> str | None:
    with repo:
        q = text("""
        select path from files join users on users.id == user_id 
        where users.username == :username and files.name == :filename
        """)
        path = repo.session.execute(q, dict(username=username, filename=filename)).first()
    if path:
        return path[0]
