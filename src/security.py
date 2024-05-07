from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from conf.config import settings
from schemas.actions_schema import CamelCaseSchema

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = int(timedelta(days=7).total_seconds())

fake_users_db = {}


class Token(CamelCaseSchema):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    sub: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False


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


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
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
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(sub=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def _create_user(repo: dict, data: SignUpSchema):
    user = repo.get(data.email, None)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    hashed_pass = get_password_hash(data.password)
    data_ = data.dict()
    data_.update({"hashed_password": hashed_pass})
    user = UserInDB(**data_)
    repo[data.username] = user.dict()
    return data


@router.post("/token")
async def login_for_access_token(
    auth_data: AuthSchema,
) -> Token:
    user = authenticate_user(fake_users_db, auth_data.username, auth_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token({"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post('/signup', summary="Create new user", response_model=SignUpSchema)
async def create_user(data: SignUpSchema):
    return _create_user(fake_users_db, data)


def _verify_refresh_token(token: str):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.REFRESH_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        if id is None:
            raise credential_exception
        token_data = TokenData(sub=username)
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
