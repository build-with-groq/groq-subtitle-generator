import os
import mimetypes
import subprocess
import json
from typing import Optional, Dict, Any
from fastapi import UploadFile
import ffmpeg
from pathlib import Path

from models.requests import FileInfo
from utils.config import get_settings

def validate_video_file(file: UploadFile) -> bool:
    """
    validate uploaded video file format and type
    """
    settings = get_settings()
    
    if not file.filename:
        return False
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.supported_video_formats:
        return False
    
    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type and not mime_type.startswith('video/'):
        return False
    
    return True

def get_file_info(file_path: str) -> FileInfo:
    """
    extract video file information using ffmpeg.probe
    """
    try:
        # file size
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'video'), None)
        
        duration = None
        format_name = None
        resolution = None
        fps = None
        
        if 'format' in probe:
            duration = float(probe['format'].get('duration', 0))
            format_name = probe['format'].get('format_name', 'unknown')
        
        if video_stream:
            width = video_stream.get('width')
            height = video_stream.get('height')
            if width and height:
                resolution = f"{width}x{height}"
            
            # calculate FPS
            fps_str = video_stream.get('r_frame_rate', '0/1')
            if '/' in fps_str:
                num, den = fps_str.split('/')
                if int(den) != 0:
                    fps = float(num) / float(den)
        
        return FileInfo(
            filename=filename,
            size=file_size,
            duration=duration,
            format=format_name,
            resolution=resolution,
            fps=fps
        )
        
    except Exception as e:
        return FileInfo(
            filename=os.path.basename(file_path),
            size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
        )

def get_video_duration(file_path: str) -> Optional[float]:
    """
    get video duration in seconds using ffprobe
    """
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        
        return None
    except Exception:
        return None

def is_video_file(file_path: str) -> bool:
    """
    check if file is a valid video file
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_streams = [stream for stream in probe['streams'] 
                        if stream['codec_type'] == 'video']
        return len(video_streams) > 0
    except Exception:
        return False

def get_video_codec(file_path: str) -> Optional[str]:
    """
    get video codec information
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'video'), None)
        if video_stream:
            return video_stream.get('codec_name')
        return None
    except Exception:
        return None

def ensure_directory_exists(directory: str) -> None:
    """
    create directory if it doesn't exist
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

def clean_filename(filename: str) -> str:
    """
    clean filename to remove invalid characters
    """
    import re
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return cleaned

def get_safe_filename(base_name: str, extension: str, directory: str) -> str:
    """
    generate a safe filename that doesn't conflict with existing files
    """
    counter = 1
    base_path = os.path.join(directory, f"{base_name}.{extension}")
    
    while os.path.exists(base_path):
        base_path = os.path.join(directory, f"{base_name}_{counter}.{extension}")
        counter += 1
    
    return base_path

def format_file_size(size_bytes: int) -> str:
    """
    format file size in human-readable format
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def format_duration(seconds: float) -> str:
    """
    format duration in HH:MM:SS format
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def check_ffmpeg_installed() -> bool:
    """
    check if ffmpeg is installed and available
    """
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_disk_space(directory: str, required_space: int) -> bool:
    """
    check if there's enough disk space for processing
    """
    try:
        stat = os.statvfs(directory)
        available_space = stat.f_bavail * stat.f_frsize
        return available_space >= required_space
    except Exception:
        return True  