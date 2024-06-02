import dataclasses
import uuid
from enum import Enum

from fastapi import FastAPI, UploadFile, File, Depends, APIRouter, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import FileResponse, JSONResponse, Response

import models
from async_tasks import create_task, get_result_task
from conf.config import BASE_DIR, settings
from repository import Repository
from schemas.actions_schema import VideoEditing
from security import router as auth_router, get_current_user, get_content_maker
from services import handlers
from services.handlers import transcript_audio_file
from utils.video import get_youtube_video_formats, YouTubeDlOptions

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
content_maker_video_router = APIRouter(prefix="/video")
file_router = APIRouter(prefix='/files')

if settings.SECURITY_ENABLED:
    video_router.dependencies.append(Depends(get_current_user))
    file_router.dependencies.append(Depends(get_current_user))
    content_maker_video_router.dependencies.append(Depends(get_content_maker))

STORAGE_DIR = BASE_DIR / settings.STORAGE_NAME
repository = Repository()


class AvailableFormats(str, Enum):
    mp4 = 'mp4'
    wav = 'wav'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


def _check_available_formats(filename: uuid.UUID):
    with repository:
        name = repository.get_file_by_uuid(filename).name
    format_ = name.split('.')[1]
    if not AvailableFormats.has_value(format_):
        raise HTTPException(status_code=422, detail=[
            {"type": "UnsupportedFormat",
             "loc": "query.filename",
             "msg": f'Unsupported format - {format_}'},
        ])
    return filename


# Files
@app.get("/files/{id}")
async def get_file(id: uuid.UUID):
    file = handlers.get_file_by_uuid(repository, id)
    if not file:
        raise HTTPException(status_code=404, detail="File is not exists")
    return FileResponse(path=file.path)


@file_router.delete("/{id}")
async def delete_file(id: uuid.UUID,
                      current_user=Depends(get_current_user)):
    handlers.delete_file(repository, id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@file_router.post("/generate-id")
async def get_confirmation(filename: str):
    id = uuid.uuid4()
    handlers.update_file_uuid_by_name(repository, id, filename)
    return id


@video_router.post("/transcribing-audio-by-notes")
async def exact_notes_from_audio(file_id: uuid.UUID = Depends(_check_available_formats),
                                 current_user=Depends(get_current_user)):
    task_id = transcript_audio_file(repository, file_id, current_user.id)

    if not task_id:
        raise HTTPException(status_code=404)

    return JSONResponse(content={'taskId': str(task_id)})


@file_router.get("/")
async def get_available_uploading_files(current_user=Depends(get_current_user)):
    with repository:
        files = repository.get_user_available_files(current_user.username)
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


@content_maker_video_router.post("/tag")
async def add_tag():
    pass


@content_maker_video_router.delete("/tag")
async def delete_tag():
    pass


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
async def crop_video_file(editing: VideoEditing,
                          filename: uuid.UUID = Depends(_check_available_formats),
                          current_user=Depends(get_current_user)):
    task_id = create_task(func=handlers.edit_user_video, kwargs={'editing': editing,
                                                                 'user_id': current_user.id,
                                                                 'file_uuid': filename})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.post("/exacting-audio")
async def exact_audio_from_video_file(filename: uuid.UUID = Depends(_check_available_formats),
                                      current_user=Depends(get_current_user)):
    task_id = create_task(func=handlers.extract_user_audio_from_video_file, kwargs={'user_id': current_user.id,
                                                                                    "file_uuid": filename})
    return JSONResponse(content={'taskId': str(task_id)})


@video_router.post("/transcribing-audio")
async def exact_text_from_audio(filename: uuid.UUID = Depends(_check_available_formats),
                                current_user=Depends(get_current_user)):
    task_id = create_task(func=handlers.transcribe_text_from_audio_file, kwargs={'file_uuid': filename,
                                                                                 'user_id': current_user.id})

    return JSONResponse(content={'taskId': str(task_id)})


@dataclasses.dataclass
class Interval:
    note: str
    frequency: float
    start: float = 0
    end: float = 0


@dataclasses.dataclass
class NotesSegmentSchema:
    status: str
    data: list[Interval] | None


def _form_intervals(notes_data: list[tuple[float, str, float]]) -> list[Interval]:
    intervals = []
    for idx, items in enumerate(notes_data):
        time, note, freq = items

        if not intervals:
            if note:
                intervals.append(Interval(note=note, start=time, frequency=freq))
            continue

        last_interval = intervals[-1]

        if idx + 1 == len(notes_data):
            if note and not last_interval.end:
                last_interval.end = round(time - 0.01, 2)
                intervals[-1] = last_interval
            break

        if note != last_interval.note:
            if not last_interval.end:
                last_interval.end = round(time - 0.01, 2)
                intervals[-1] = last_interval
            if note:
                intervals.append(Interval(note=note, start=time, frequency=freq))
    return intervals


@video_router.get("/notes_segment/{task_id}", response_model=NotesSegmentSchema)
async def get_notes_segment(task_id: str):
    result = get_result_task(task_id)
    intervals = [dataclasses.asdict(interval) for interval in _form_intervals(result)] if result else None
    return NotesSegmentSchema(**{'status': 'ok' if result else 'processing',
                                 'data': intervals})


# Get tasks result
@video_router.get("/tasks/result")
async def get_task_result(task_id: str = Query(alias="taskId")):
    result = get_result_task(task_id)
    return JSONResponse(content={'status': 'ok' if result else 'processing', 'result': result})

app.include_router(video_router)
app.include_router(auth_router)
app.include_router(file_router)
app.include_router(content_maker_video_router)
