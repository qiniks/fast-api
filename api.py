from datetime import datetime
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip
# server/main.py
import uuid
import shutil
import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

def remove_file(path: str):
    try:
        os.remove(path)
    except Exception as e:
        print(f"Ошибка при удалении файла {path}: {e}")

@app.post("/compress-video")
async def compress_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        start = datetime.now()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            input_path = temp_input.name
            content = await file.read()
            temp_input.write(content)
        
        output_fd, output_path = tempfile.mkstemp(suffix="_compressed.mp4")
        os.close(output_fd)
        
        clip = VideoFileClip(input_path)
        original_width, original_height = clip.size

        
        # max_dimension = 720


        # if original_width > max_dimension or original_height > max_dimension:
        #     if original_width >= original_height:
        #         new_width = max_dimension
        #         new_height = int(original_height * (max_dimension / original_width))
        #         clip = clip.resize(newsize=(new_width, new_height))
        #     else:
        #         new_height = max_dimension
        #         new_width = int(original_width * (max_dimension / original_height))
        #         clip = clip.resize(newsize=(new_width, new_height))

        # print(original_height, original_width)
        # print(new_height, new_width)

        # if original_height == 1080 and original_width == 1920:
        #     new_width = 1280
        #     new_height = 720
        #     clip = clip.resize(newsize=(new_width, new_height))
        # elif original_height == 1920 and original_width == 1080:
        #     new_height = 1280
        #     new_width = 720
        #     clip = clip.resize(newsize=(new_width, new_height))
        
       
        
        clip.write_videofile(
            output_path,
            codec="libx264",
            ffmpeg_params=[
                "-crf", "38", 
                "-preset", "slow"],
            bitrate="400k",  
            audio_codec="aac",
            threads=8,
        )
        
        # clip_resized.close()
        clip.close()
        
        background_tasks.add_task(remove_file, input_path)
        background_tasks.add_task(remove_file, output_path)

        end = datetime.now()
        print("compression time", end - start)
        print(clip.size)

        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename="compressed.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сжатии видео: {str(e)}")


TEMP_DIR = "/tmp"  # или другая подходящая директория

@app.post("/compress_video2/")
async def compress_video(file: UploadFile = File(...)):
    # Сохраняем исходный файл во временную директорию
    input_filename = f"{uuid.uuid4()}_{file.filename}"
    input_filepath = os.path.join(TEMP_DIR, input_filename)
    
    with open(input_filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Задаем имя для выходного файла
    output_filename = f"compressed_{uuid.uuid4()}_{file.filename}"
    output_filepath = os.path.join(TEMP_DIR, output_filename)
    
    # Формируем команду ffmpeg для сжатия:
    # Пример: использовать кодек libx264 с CRF=28 для видео и aac для аудио
    cmd = [
        "ffmpeg",
        "-i", input_filepath,
        "-c:v", "libx264",
        "-preset", "veryfast",  # можно менять: ultrafast, superfast, veryfast, faster, fast, medium, slow, veryslow
        "-crf", "28",  # качество: чем выше значение, тем ниже качество и меньше размер
        "-c:a", "aac",
        "-b:a", "128k",
        output_filepath,
        "-y"  # перезаписывать без подтверждения
    ]
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if process.returncode != 0:
        # Очистка временных файлов
        os.remove(input_filepath)
        raise HTTPException(status_code=500, detail=f"ffmpeg error: {process.stderr.decode('utf-8')}")
    
    # Удаляем исходный файл (если не нужен)
    os.remove(input_filepath)
    
    # Отдаем сжатый файл клиенту
    return FileResponse(output_filepath, media_type="video/mp4", filename=f"compressed_{file.filename}")
