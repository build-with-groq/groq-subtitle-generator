from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Optional, Dict
import asyncio
import json
from datetime import datetime
import io

from services.video_processing_service import VideoProcessingService
from utils.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Subtitle Generator", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

video_service = VideoProcessingService()
settings = get_settings()

active_jobs: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {"message": "Video Subtitle Generator API"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and return job ID"""
    try:
        # validate
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # read video data
        video_data = await file.read()
        
        # check file size 
        if len(video_data) > settings.max_file_size:
            max_size_mb = settings.max_file_size / (1024 * 1024)
            raise HTTPException(status_code=400, detail=f"File size exceeds {max_size_mb:.0f}MB limit")
        
        import uuid
        job_id = str(uuid.uuid4())
        
        active_jobs[job_id] = {
            "status": "uploaded",
            "filename": file.filename,
            "video_data": video_data,
            "created_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        logger.info(f"Video uploaded successfully: {file.filename} (Job ID: {job_id})")
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "size": len(video_data),
            "status": "uploaded"
        }
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/{job_id}")
async def process_video(
    job_id: str,
    background_tasks: BackgroundTasks,
    target_language: str = Form(...),
    source_language: Optional[str] = Form(None)
):
    """Start video processing"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        if job["status"] != "uploaded":
            raise HTTPException(status_code=400, detail="Job not ready for processing")
        
        job["target_language"] = target_language
        
        background_tasks.add_task(
            process_video_background,
            job_id,
            job["video_data"],
            target_language,
            source_language
        )
        
        logger.info(f"Started processing for job: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "processing_started",
            "message": "Video processing started"
        }
        
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_background(job_id: str, video_data: bytes, target_language: str, source_language: Optional[str]):
    """Background task for video processing"""
    try:
        job = active_jobs[job_id]
        
        job["progress"] = 20
        job["status"] = "extracting_audio"
        
        async with video_service.temporary_file(suffix=".mp4") as temp_video_path:
            with open(temp_video_path, 'wb') as f:
                f.write(video_data)
            
            async with video_service.temporary_file(suffix=".wav") as temp_audio_path:
                await video_service._extract_audio(temp_video_path, temp_audio_path)
                
                job["progress"] = 50
                job["status"] = "transcribing"
                
                logger.info(f"Starting transcription for job {job_id}")
                transcription_result = await video_service.transcription_service.transcribe_audio(
                    temp_audio_path, 
                    language=source_language
                )
                
                logger.info(f"Transcription completed for job {job_id}. Segments: {len(transcription_result.segments)}, Text length: {len(transcription_result.text)}")
                
                # detect language if not provided
                if not source_language:
                    source_language = transcription_result.detected_language or "en"
                
                # store transcription result for user review
                job["transcription_result"] = {
                    "text": transcription_result.text,
                    "segments": [
                        {
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text,
                            "confidence": seg.confidence
                        } for seg in transcription_result.segments
                    ],
                    "detected_language": transcription_result.detected_language,
                    "confidence": transcription_result.confidence
                }
                job["source_language"] = source_language
                job["status"] = "transcription_complete"
                job["progress"] = 60
                
                logger.info(f"Transcription completed for job {job_id}, waiting for user review")
                
    except Exception as e:
        logger.error(f"Error processing video {job_id}: {str(e)}")
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = str(e)
            active_jobs[job_id]["progress"] = 0

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": job.get("error", ""),
            "filename": job.get("filename", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transcription/{job_id}")
async def get_transcription(job_id: str):
    """Get transcription result for user review"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        if job["status"] != "transcription_complete":
            raise HTTPException(status_code=400, detail="Transcription not ready for review")
        
        return {
            "job_id": job_id,
            "transcription": job["transcription_result"],
            "source_language": job["source_language"],
            "target_language": job["target_language"],
            "filename": job["filename"]
        }
        
    except Exception as e:
        logger.error(f"Error getting transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcription/{job_id}/continue")
async def continue_with_transcription(
    job_id: str,
    background_tasks: BackgroundTasks,
    transcription: dict
):
    """Continue processing with edited transcription"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        if job["status"] != "transcription_complete":
            raise HTTPException(status_code=400, detail="Job not ready for transcription continuation")
        
        # start background processing with edited transcription
        background_tasks.add_task(
            continue_processing_after_transcription,
            job_id,
            transcription
        )
        
        logger.info(f"Continuing processing with edited transcription for job: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "processing_continued",
            "message": "Processing continued with edited transcription"
        }
        
    except Exception as e:
        logger.error(f"Error continuing with transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def continue_processing_after_transcription(job_id: str, edited_transcription: dict):
    """Continue processing after user has reviewed/edited transcription"""
    try:
        job = active_jobs[job_id]
        
        # recreate transcription result from edited data
        from models.requests import TranscriptionResult, TranscriptionSegment
        
        segments = [
            TranscriptionSegment(
                start=seg["start"],
                end=seg["end"], 
                text=seg["text"],
                confidence=seg["confidence"]
            ) for seg in edited_transcription["segments"]
        ]
        
        transcription_result = TranscriptionResult(
            text=edited_transcription["text"],
            segments=segments,
            detected_language=edited_transcription["detected_language"],
            confidence=edited_transcription["confidence"]
        )
        
        job["status"] = "translating"
        job["progress"] = 70
        
        source_language = job["source_language"]
        target_language = job["target_language"]
        
        if source_language != target_language:
            translated_segments = await video_service.translation_service.translate_segments(
                transcription_result.segments, source_language, target_language
            )
            
            final_transcription = TranscriptionResult(
                text=" ".join([segment.text for segment in translated_segments]),
                segments=translated_segments,
                detected_language=source_language,
                confidence=transcription_result.confidence
            )
        else:
            final_transcription = transcription_result
        
        job["status"] = "generating_subtitles"
        job["progress"] = 80
        
        # generate subtitles and render video
        srt_content = await video_service.subtitle_service.generate_srt_content(final_transcription)
        
        video_data = job["video_data"]
        
        async with video_service.temporary_file(suffix=".mp4") as temp_video_path:
            with open(temp_video_path, 'wb') as f:
                f.write(video_data)
            
            async with video_service.temporary_file(suffix=".srt") as temp_subtitle_path:
                with open(temp_subtitle_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                
                job["status"] = "rendering_video"
                job["progress"] = 90
                
                result_video_bytes = await video_service._render_video_to_bytes(temp_video_path, temp_subtitle_path)
        
        # update job with result
        job["status"] = "completed"
        job["progress"] = 100
        job["result_video"] = result_video_bytes
        job["completed_at"] = datetime.now().isoformat()
        
        # Clear video data to save memory
        del job["video_data"]
        del job["transcription_result"]
        
        logger.info(f"Job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Error continuing processing for job {job_id}: {str(e)}")
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = str(e)
            active_jobs[job_id]["progress"] = 0

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download processed video with subtitles"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if "result_video" not in job:
            raise HTTPException(status_code=404, detail="Processed video not found")
        
        video_bytes = job["result_video"]
        
        original_filename = job["filename"]
        name, ext = original_filename.rsplit('.', 1)
        download_filename = f"{name}_subtitled.{ext}"
        
        def cleanup_job():
            if job_id in active_jobs:
                del active_jobs[job_id]
                logger.info(f"Cleaned up job from memory: {job_id}")
        
        def generate():
            yield video_bytes
            cleanup_job()
        
        return StreamingResponse(
            generate(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}",
                "Content-Length": str(len(video_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/preview/{job_id}")
async def preview_video(job_id: str):
    """Stream processed video for preview"""
    try:
        if job_id not in active_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = active_jobs[job_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if "result_video" not in job:
            raise HTTPException(status_code=404, detail="Processed video not found")
        
        video_bytes = job["result_video"]
        
        return StreamingResponse(
            io.BytesIO(video_bytes),
            media_type="video/mp4",
            headers={
                "Content-Length": str(len(video_bytes)),
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming video preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 