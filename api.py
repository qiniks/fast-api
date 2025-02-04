from datetime import datetime
import os
import tempfile
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
        start = datetime.now()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            input_path = temp_input.name
            content = await file.read()
            temp_input.write(content)
        
        output_fd, output_path = tempfile.mkstemp(suffix="_compressed.mp4")
        os.close(output_fd)
        
        clip = VideoFileClip(input_path)
        original_height, original_width = clip.size

        
        # max_dimension = 1280

        # if original_width >= original_height:
        #     new_width = max_dimension
        #     new_height = int(original_height * (max_dimension / original_width))
        # else:
        #     new_height = max_dimension
        #     new_width = int(original_width * (max_dimension / original_height))

        # print(original_height, original_width)
        # print(new_height, new_width)
        
        # clip_resized = clip.resize(newsize=(new_width, new_height))
        
        clip.write_videofile(
            output_path,
            codec="libx264",
            ffmpeg_params=["-crf", "23"],
            bitrate="400k",  
            preset="slow",
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
