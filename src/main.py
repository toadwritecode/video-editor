from enum import Enum

from fastapi import FastAPI, UploadFile, File, Depends, APIRouter, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, JSONResponse

import models
from async_tasks import create_task, get_result_task
from conf.config import BASE_DIR, settings
from repository import Repository
from schemas.actions_schema import VideoEditing
from security import router as auth_router, get_current_user
from services import handlers
from queries import queries
from utils.video import transcribe_audio, get_youtube_video_formats, YouTubeDlOptions
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
    video_router.dependencies.append(Depends(get_current_user))
    file_router.dependencies.append(Depends(get_current_user))

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME
repository = Repository()


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
async def get_file(filename: str, current_user=Depends(get_current_user)):
    path = queries.get_path_user_file(repository, current_user.username, filename)
    if not path:
        raise HTTPException(status_code=404, detail="File is not exists")
    return FileResponse(path=path)


@file_router.get("/")
async def get_available_uploading_files(current_user=Depends(get_current_user)):
    files = queries.get_user_available_files(repository, current_user.username)
    return JSONResponse(content=files)


@file_router.post("/")
async def upload_file(file: UploadFile = File(), current_user: models.User = Depends(get_current_user)):
    try:
        filename = handlers.save_user_file(repository, current_user.username, file)
        return JSONResponse(content={'status': 'ok', "filename": filename})
    except models.FileError as exc:
        raise HTTPException(status_code=400, detail=[
            {"type": exc.__class__.__name__,
             "loc": "file",
             "msg": str(exc)},
        ])


# YouTube
@file_router.get("/youtube/")
async def download_video_from_youtube(link: str,
                                      format_: str | None = Query(alias="format", default="mp4"),
                                      current_user=Depends(get_current_user)):
    options = YouTubeDlOptions(format=format_)
    task_id = create_task(func=handlers.save_user_file_from_youtube, kwargs={
                                                                    'link': link, "options": options,
                                                                    'username': current_user.username})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.get("/youtube/available_formats")
async def get_available_formats(link: str):
    formats = get_youtube_video_formats(link)
    return JSONResponse(content={"data": formats})


# Editing
@video_router.post("/crop")
async def crop_video_file(editing: VideoEditing, filename: str = Depends(_check_available_formats),
                          current_user=Depends(get_current_user)):

    task_id = create_task(func=handlers.edit_user_video, kwargs={'editing': editing,
                                                                 'username': current_user.username,
                                                                 'filename': filename})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.post("/exacting-audio")
async def exact_audio_from_video_file(filename: str = Depends(_check_available_formats),
                                      current_user=Depends(get_current_user)):
    task_id = create_task(func=handlers.extract_user_audio_from_video_file,
                          kwargs={'username': current_user.username, "filename": filename})
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


app.include_router(video_router)
app.include_router(auth_router)
app.include_router(file_router)
app.include_router(auth_router)
