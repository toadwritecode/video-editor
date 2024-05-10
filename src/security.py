from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

import models
from conf.config import settings
from repository import Repository
from schemas.actions_schema import CamelCaseSchema

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = int(timedelta(days=7).total_seconds())

fake_users_db = {}
auth_repo = Repository()


class AvailableRoles(str, Enum):
    default = "default"
    content_maker = "content_maker"


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    role: AvailableRoles = AvailableRoles.default
    full_name: str | None = None

    class Config:
        use_enum_values = True


class Token(CamelCaseSchema):
    access_token: str
    refresh_token: str
    token_type: str
    data: User


class SignUpSchema(User, CamelCaseSchema):
    password: str


class UserInDB(User):
    hashed_password: str


class AuthSchema(CamelCaseSchema):
    username: str
    password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix='/authenticate')


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(repo, username: str):
    with repo:
        user = repo.get(username)
    return user


def authenticate_user(repo, username: str, password: str) -> bool | models.User:
    user = get_user(repo, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_KEY, ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(auth_repo, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def _create_user(repo, data: SignUpSchema):
    with repo:
        user = repo.get(data.username)

        if user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exist"
            )
        hashed_pass = get_password_hash(data.password)
        data_ = data.dict()

        data_.update({"password": hashed_pass})

        user = models.User(**data_)
        repo.add(user)
        repo.commit()
        return data


@router.post("/token")
async def login_for_access_token(
    auth_data: AuthSchema,
) -> Token:
    user = authenticate_user(auth_repo, auth_data.username, auth_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token({"username": user.username})
    user_schema = User(username=user.username,
                       email=user.email,
                       role=user.role,
                       full_name=user.full_name)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", data=user_schema)


@router.post('/signup', summary="Create new user", response_model=SignUpSchema)
async def create_user(data: SignUpSchema):
    return _create_user(auth_repo, data)


def _verify_refresh_token(token: str):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.REFRESH_KEY, algorithms=ALGORITHM)
        username: str = payload.get("username")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    return token_data


@router.get("/refresh")
def get_new_access_token(token: str):
    refresh_data = _verify_refresh_token(token)

    new_access_token = create_access_token(refresh_data.dict())
    return {
        "accessToken": new_access_token,
        "tokenType": "Bearer"
    }
