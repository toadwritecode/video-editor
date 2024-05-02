import os
from enum import Enum

from fastapi import FastAPI, UploadFile, File, Depends, APIRouter, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse

from async_tasks import create_task, get_result_task
from conf.config import BASE_DIR, settings
from schemas.actions_schema import VideoEditing
from security import get_basic_auth, authenticate_user
from services.video_handlers import extract_audio_from_video_file, transcribe_audio, edit_video, \
    get_youtube_video_formats, YouTubeDlOptions, download_youtube_video

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# private
video_router = APIRouter(prefix='/video')
file_router = APIRouter(prefix='/files')

if settings.SECURITY_ENABLED:
    video_router.dependencies.append(Depends(get_basic_auth))
    file_router.dependencies.append(Depends(get_basic_auth))

# public
auth_router = APIRouter()

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME


class AvailableFormats(str, Enum):
    mp4 = 'mp4'
    wav = 'wav'

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


# Files
@file_router.get("/{filename}")
async def get_file(filename: str):
    path = str(STORAGE_DIR / filename)
    return FileResponse(path=path)


@file_router.get("/")
async def get_available_uploading_files():
    return JSONResponse(
        content=[{"name": file, "path": os.path.abspath(file)} for file in os.listdir(STORAGE_DIR)]
    )


@file_router.post("/")
async def upload_file(file: UploadFile = File()):
    filename = file.filename
    with open(STORAGE_DIR / filename, "wb") as f:
        content = file.file.read()
        f.write(content)
    return JSONResponse(content={'status': 'ok', "filename": filename})


# YouTube
@file_router.get("/youtube/")
async def download_video_from_youtube(link: str,
                                      format_: str | None = Query(alias="format", default="mp4")):
    options = YouTubeDlOptions(format=format_)
    task_id = create_task(func=download_youtube_video, kwargs={'link': link, "options": options})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.get("/youtube/available_formats")
async def get_available_formats(link: str):
    formats = get_youtube_video_formats(link)
    return JSONResponse(content={"data": formats})


# Editing
@video_router.post("/crop")
async def crop_video_file(editing: VideoEditing, filename: str = Depends(_check_available_formats)):
    path = str(STORAGE_DIR / filename)

    task_id = create_task(func=edit_video, kwargs={'editing': editing, 'path': path})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.post("/exacting-audio")
async def exact_audio_from_video_file(filename: str = Depends(_check_available_formats)):
    path = str(STORAGE_DIR / filename)

    task_id = create_task(func=extract_audio_from_video_file, kwargs={'path': path})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.post("/transcribing-audio")
async def exact_text_from_audio(filename: str = Depends(_check_available_formats)):
    path = str(STORAGE_DIR / filename)

    task_id = create_task(func=transcribe_audio, kwargs={'path': path})
    return JSONResponse(content={'taskId': str(task_id)})


# Get tasks result

@video_router.get("/tasks/result")
async def get_task_result(task_id: str = Query(alias="taskId")):
    result = get_result_task(task_id)
    return JSONResponse(content={'status': 'ok' if result else 'processing', 'result': result})


# Authorize
@auth_router.get("/token")
async def get_token(username: str, password: str):
    token = authenticate_user(username, password)
    return JSONResponse(content={"token": token})


app.include_router(video_router)
app.include_router(auth_router)
app.include_router(file_router)
