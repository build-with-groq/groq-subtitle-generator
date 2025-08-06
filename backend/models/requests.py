from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    GENERATING_SUBTITLES = "generating_subtitles"
    RENDERING_VIDEO = "rendering_video"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessVideoRequest(BaseModel):
    target_language: str
    source_language: Optional[str] = None
    subtitle_format: Optional[str] = "srt" 

class VideoProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    message: str = ""
    file_path: Optional[str] = None
    output_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    target_language: Optional[str] = None
    source_language: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        use_enum_values = True

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: Optional[float] = None

class TranscriptionResult(BaseModel):
    text: str
    segments: List[TranscriptionSegment]
    detected_language: Optional[str] = None
    confidence: Optional[float] = None

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str
    context: Optional[str] = None

class TranslationResult(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: Optional[float] = None

class SubtitleEntry(BaseModel):
    start_time: str
    end_time: str
    text: str
    index: int

class FileInfo(BaseModel):
    filename: str
    size: int
    duration: Optional[float] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None 