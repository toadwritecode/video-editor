import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette import status

from conf.config import settings

security = HTTPBasic()


def get_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):

    # сверка по хешу знач
    is_user_ok = secrets.compare_digest(credentials.username, settings.AUTH_API_LOGIN)
    is_pass_ok = secrets.compare_digest(credentials.password, settings.AUTH_API_PASSWORD)

    if not is_user_ok or not is_pass_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Basic"},
        )
