import secrets
from base64 import b64encode

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette import status

from conf.config import settings

security = HTTPBasic()


def check_auth(username: str, password: str):
    # сверка по хешу знач
    is_user_ok = secrets.compare_digest(username, settings.AUTH_API_LOGIN)
    is_pass_ok = secrets.compare_digest(password, settings.AUTH_API_PASSWORD)

    if not is_user_ok or not is_pass_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def get_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    check_auth(credentials.username, credentials.password)


def authenticate_user(username: str, password: str):
    check_auth(username, password)
    return f'Basic {b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")}'
