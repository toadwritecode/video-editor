from fastapi import FastAPI, UploadFile, Depends, File
from starlette.responses import FileResponse

from schemas import VideoCutRequest
from services import cut_video_file


app = FastAPI()


@app.post("/video/crop")
async def crop_video_file(request: VideoCutRequest = Depends(), file: UploadFile = File()):
    var = file.filename
    with open(var, "wb") as f:
        content = file.file.read()
        f.write(content)

    cut_video_file(file.filename, request.cut_from, request.cut_to)
    return FileResponse(file.filename.replace(".mp4", "") + "_cropped.mp4")
