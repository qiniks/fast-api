from datetime import datetime
import os
import shutil
import subprocess
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI()


def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Ошибка при удалении файла {path}: {e}")


@app.post("/compress-video")
async def compress_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
):
    input_filename = f"temp_{uuid.uuid4().hex}_{video.filename}"
    output_filename = f"compressed_{uuid.uuid4().hex}_{video.filename}"

    s = datetime.now()

    try:
        with open(input_filename, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Не удалось сохранить видеофайл.")

    command = [
        "ffmpeg",
        "-i", input_filename,
        "-vcodec", "libx264",
        "-crf", "40",
        "-preset", "veryfast",
        "-movflags", "faststart",
        output_filename,
        "-y"  
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
    except subprocess.CalledProcessError as e:
        remove_file(input_filename)
        raise HTTPException(status_code=500, detail=f"Ошибка компрессии видео: {e.stderr.decode()}")

    remove_file(input_filename)

    background_tasks.add_task(remove_file, output_filename)
    
    end = datetime.now()

    print(end-s)
    return FileResponse(
        output_filename,
        media_type="video/mp4",
        filename=output_filename
    )
