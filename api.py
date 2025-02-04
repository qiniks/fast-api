import os
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
        start = datetime.datetime.now()
        print(start)
        # Сохраняем исходное видео во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            input_path = temp_input.name
            content = await file.read()
            temp_input.write(content)
        
        # Создаем временный файл для сжатого видео
        output_fd, output_path = tempfile.mkstemp(suffix="_compressed.mp4")
        os.close(output_fd)
        
        # Открываем видео с помощью MoviePy
        clip = VideoFileClip(input_path)
        
        # Пример сжатия: изменение разрешения (например, до 480p) и уменьшение битрейта
        # Можно настроить эти параметры под свои задачи
        clip_resized = clip.resize(height=480)
        
        # Сохраняем сжатое видео
        clip_resized.write_videofile(
            output_path,
            codec="libx264",
            preset="veryfast",
            bitrate="400k",      # Указываем битрейт для контроля размера и качества
            audio_codec="aac",
            threads=8,
        )
        
        # Закрываем клипы
        clip_resized.close()
        clip.close()
        
        # Удаляем временный входной файл в фоне
        background_tasks.add_task(remove_file, input_path)
        # Обратите внимание: выходной файл будет удалён после того, как FileResponse отправит его клиенту.
        background_tasks.add_task(remove_file, output_path)

        end = datetime.datetime.now()

        print(start)        
        print(end)
        print(end - start)
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename="compressed.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сжатии видео: {str(e)}")
