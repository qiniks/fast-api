import os
import subprocess
import tempfile
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip

app = FastAPI()

def remove_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"Ошибка при удалении файла {path}: {e}")

@app.post("/compress-video")
async def compress_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        # Use in-memory temporary files (Linux specific)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            input_path = temp_input.name
            content = await file.read()
            temp_input.write(content)

        output_fd, output_path = tempfile.mkstemp(suffix="_compressed.mp4")
        os.close(output_fd)

        # Direct FFmpeg processing
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vf', 'scale=-2:480',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-movflags', '+faststart',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-threads', str(os.cpu_count() or 4),
            output_path
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        # Cleanup
        background_tasks.add_task(remove_file, input_path)
        background_tasks.add_task(remove_file, output_path)

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="compressed.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сжатии видео: {str(e)}")