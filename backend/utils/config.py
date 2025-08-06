import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
    groq_whisper_model: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")
    
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB default
    supported_video_formats: list = [
        "mp4", "mov", "avi"
    ]
    
    temp_dir: str = os.getenv("TEMP_DIR", "temp")
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    
    
    # Supported languages
    supported_languages: dict = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese",
        "nl": "Dutch",
        "sv": "Swedish",
        "no": "Norwegian",
        "da": "Danish",
        "fi": "Finnish",
        "pl": "Polish",
        "tr": "Turkish",
        "cs": "Czech",
        "hu": "Hungarian",
        "ro": "Romanian",
        "bg": "Bulgarian",
        "hr": "Croatian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "et": "Estonian",
        "lv": "Latvian",
        "lt": "Lithuanian",
        "mt": "Maltese",
        "ga": "Irish",
        "cy": "Welsh",
        "eu": "Basque",
        "ca": "Catalan",
        "gl": "Galician",
        "is": "Icelandic",
        "mk": "Macedonian",
        "sq": "Albanian",
        "be": "Belarusian",
        "uk": "Ukrainian",
        "he": "Hebrew",
        "fa": "Persian",
        "ur": "Urdu",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "ml": "Malayalam",
        "kn": "Kannada",
        "gu": "Gujarati",
        "mr": "Marathi",
        "ne": "Nepali",
        "si": "Sinhala",
        "my": "Burmese",
        "km": "Khmer",
        "lo": "Lao",
        "ka": "Georgian",
        "am": "Amharic",
        "sw": "Swahili",
        "zu": "Zulu",
        "af": "Afrikaans",
        "ms": "Malay",
        "tl": "Filipino",
        "id": "Indonesian"
    }
    
    # FFmpeg settings
    ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    subtitle_font: str = os.getenv("SUBTITLE_FONT", "Arial")
    subtitle_font_size: int = int(os.getenv("SUBTITLE_FONT_SIZE", "24"))
    subtitle_color: str = os.getenv("SUBTITLE_COLOR", "white")
    subtitle_outline_color: str = os.getenv("SUBTITLE_OUTLINE_COLOR", "black")
    subtitle_outline_width: int = int(os.getenv("SUBTITLE_OUTLINE_WIDTH", "2"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def validate_groq_key():
    """Validate that Groq API key is provided"""
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")
    return True

def get_language_code(language_name: str) -> str:
    """Get language code from language name"""
    settings = get_settings()
    for code, name in settings.supported_languages.items():
        if name.lower() == language_name.lower():
            return code
    return language_name.lower()

def get_language_name(language_code: str) -> str:
    """Get language name from language code"""
    settings = get_settings()
    return settings.supported_languages.get(language_code.lower(), language_code) 