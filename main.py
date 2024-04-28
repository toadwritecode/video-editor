from fastapi import FastAPI, UploadFile, File, Depends, APIRouter, Query
from starlette.responses import FileResponse, JSONResponse

from async_tasks import create_task, get_result_task
from conf.config import BASE_DIR
from schemas.actions_schema import CutSchema
from security import get_basic_auth, authenticate_user
from services.video_handlers import cut_video_file, extract_audio_from_video_file, transcribe_audio

app = FastAPI()

video_router = APIRouter(dependencies=[Depends(get_basic_auth)], prefix='/video')
auth_router = APIRouter()
VIDEO_STORE_DIR = BASE_DIR / "video"


@video_router.post("/cropping")
async def crop_video_file(cut: CutSchema, filename: str):
    path = str(VIDEO_STORE_DIR / filename)
    cropped_video_path = cut_video_file(path, cut.cut_from, cut.cut_to)
    return FileResponse(cropped_video_path)


@video_router.post("/uploading")
async def upload_video_file(file: UploadFile = File()):
    filename = file.filename
    with open(VIDEO_STORE_DIR / filename, "wb") as f:
        content = file.file.read()
        f.write(content)
    return JSONResponse(status_code=200, content={'status': 'ok', "filename": filename})


@video_router.post("/exacting-audio")
async def exact_audio_from_video_file(filename: str):
    path = str(VIDEO_STORE_DIR / filename)
    audio_path = extract_audio_from_video_file(path)
    return FileResponse(audio_path)


@video_router.post("/transcribing-audio")
async def exact_audio_from_video_file(filename: str):
    path = str(VIDEO_STORE_DIR / filename)
    task_id = create_task(func=transcribe_audio, kwargs={'path': path})
    return JSONResponse(status_code=201, content={'taskId': str(task_id)})


@video_router.get("/transcribing-audio/result")
async def exact_audio_from_video_file(task_id: str = Query(alias="taskId")):
    result = get_result_task(task_id)
    return JSONResponse(status_code=201, content={'status': 'ok' if result else 'processing', 'result': result})


@auth_router.get("/token")
async def get_token(username: str, password: str):
    token = authenticate_user(username, password)
    return JSONResponse(status_code=200, content={"token": token})


app.include_router(video_router)
app.include_router(auth_router)
