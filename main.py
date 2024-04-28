from enum import Enum

from fastapi import FastAPI, UploadFile, File, Depends, APIRouter, Query, HTTPException
from starlette.responses import FileResponse, JSONResponse

from async_tasks import create_task, get_result_task
from conf.config import BASE_DIR
from schemas.actions_schema import VideoEditing
from security import get_basic_auth, authenticate_user
from services.video_handlers import extract_audio_from_video_file, transcribe_audio, edit_video

app = FastAPI()

# private
video_router = APIRouter(dependencies=[Depends(get_basic_auth)], prefix='/video')
file_router = APIRouter(dependencies=[Depends(get_basic_auth)], prefix='/uploading')

# public
auth_router = APIRouter()

VIDEO_STORE_DIR = BASE_DIR / "video"


class AvailableFormats(str, Enum):
    mp4 = 'mp4'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


def _check_available_formats(filename: str):
    format_ = filename.split('.')[1]
    if not AvailableFormats.has_value(format_):
        raise HTTPException(status_code=422, detail=[
            {"type": "UnsupportedFormat",
             "loc": "query.filename",
             "msg": f'Unsupported format - {format_}'},
        ])
    return filename


# Uploading
@file_router.get("/")
async def get_file(filename: str):
    path = str(VIDEO_STORE_DIR / filename)
    return FileResponse(path=path, status_code=200)


@file_router.post("/")
async def upload_file(file: UploadFile = File()):
    filename = file.filename
    with open(VIDEO_STORE_DIR / filename, "wb") as f:
        content = file.file.read()
        f.write(content)
    return JSONResponse(status_code=200, content={'status': 'ok', "filename": filename})


# Editing
@video_router.post("/cropping")
async def crop_video_file(editing: VideoEditing, filename: str = Depends(_check_available_formats)):
    path = str(VIDEO_STORE_DIR / filename)

    task_id = create_task(func=edit_video, kwargs={'editing': editing, 'path': path})
    return JSONResponse(status_code=201, content={'taskId': str(task_id)})


@video_router.post("/exacting-audio")
async def exact_audio_from_video_file(filename: str = Depends(_check_available_formats)):
    path = str(VIDEO_STORE_DIR / filename)

    task_id = create_task(func=extract_audio_from_video_file, kwargs={'path': path})
    return JSONResponse(status_code=201, content={'taskId': str(task_id)})


@video_router.post("/transcribing-audio")
async def exact_audio_from_video_file(filename: str = Depends(_check_available_formats)):
    path = str(VIDEO_STORE_DIR / filename)

    task_id = create_task(func=transcribe_audio, kwargs={'path': path})
    return JSONResponse(status_code=201, content={'taskId': str(task_id)})


# Get tasks result

@video_router.get("/tasks/result")
async def exact_audio_from_video_file(task_id: str = Query(alias="taskId")):
    result = get_result_task(task_id)
    return JSONResponse(status_code=201, content={'status': 'ok' if result else 'processing', 'result': result})


# Authorize
@auth_router.get("/token")
async def get_token(username: str, password: str):
    token = authenticate_user(username, password)
    return JSONResponse(status_code=200, content={"token": token})


app.include_router(video_router)
app.include_router(auth_router)
app.include_router(file_router)
