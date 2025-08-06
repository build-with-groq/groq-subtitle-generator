import os
import asyncio
import logging
from typing import List, Optional, Dict
from groq import Groq
import tempfile
import json
import re

from models.requests import TranscriptionResult, TranscriptionSegment
from utils.config import get_settings, get_language_code, validate_groq_key

logger = logging.getLogger(__name__)

class TranscriptionService:
    """transcribe audio using whisper"""
    
    def __init__(self):
        self.settings = get_settings()
        validate_groq_key()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.model = self.settings.groq_whisper_model
    
    #main public interface for transcribing audio (asynchronous method)
    async def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """transcribe audio file to text with timestamps using whisper"""
        try:
            logger.info(f"Transcribing audio: {audio_path} with model: {self.model}")
            if language:
                logger.info(f"Using specified language: {language}")
            
            #read audio file and run executor to avoid blocking 
            with open(audio_path, "rb") as file:
                audio_data = file.read()
                logger.info(f"Audio file size: {len(audio_data)} bytes")
                
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    self._transcribe_with_groq, 
                    audio_data,
                    language
                )
            
            transcription_result = self._convert_groq_result(result, language)
            
            logger.info(f"Transcription completed successfully:")
            logger.info(f"  - Text length: {len(transcription_result.text)} characters")
            logger.info(f"  - Number of segments: {len(transcription_result.segments)}")
            logger.info(f"  - Detected language: {transcription_result.detected_language}")
            logger.info(f"  - Overall confidence: {transcription_result.confidence:.2f}")
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    #this is the actual transcription method that calls the groq api
    def _transcribe_with_groq(self, audio_data: bytes, language: Optional[str] = None) -> dict:
        """perform the actual transcription"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                logger.info(f"Calling Groq API with model: {self.model}")
                
                with open(temp_file.name, "rb") as file:
                    transcription = self.client.audio.transcriptions.create(
                        file=file,
                        model=self.model,
                        language=language,
                        response_format="verbose_json",
                        temperature=0.0  
                    )
                
                os.unlink(temp_file.name)
                
                if hasattr(transcription, 'model_dump'):
                    result = transcription.model_dump()
                else:
                    result = transcription.__dict__
                
                logger.info(f"Groq API response received:")
                logger.info(f"  - Response keys: {list(result.keys())}")
                logger.info(f"  - Text length: {len(result.get('text', ''))}")
                
                if 'segments' in result:
                    logger.info(f"  - Number of segments: {len(result['segments'])}")
                else:
                    logger.warning("  - No segments in response (text-only)")
                
                return result
            
        except Exception as e:
            logger.error(f"Groq API transcription error: {str(e)}")
            raise
    
    #converts the output from the groq api to the intended format
    def _convert_groq_result(self, result: dict, expected_language: Optional[str] = None) -> TranscriptionResult:
        """Convert Groq API result to our TranscriptionResult format"""
        try:
            segments = []
            
            # handle segmented response 
            if 'segments' in result and result['segments']:
                logger.info("Processing segmented transcription")
                for i, segment in enumerate(result['segments']):
                    start_time = float(segment.get('start', 0.0))
                    end_time = float(segment.get('end', 0.0))
                    text = segment.get('text', '').strip()
                    
                    if not text:
                        logger.debug(f"Skipping empty segment {i}")
                        continue
                    
                    # random thing to check for hallucinations (not sure if this is needed)
                    if self._is_likely_hallucination(text, expected_language):
                        logger.warning(f"Potential hallucination detected in segment {i}: '{text}' - skipping")
                        continue
                    
                    # calculate confidence
                    confidence = 0.8  # default
                    if 'avg_logprob' in segment:
                        logprob = float(segment['avg_logprob'])
                        # convert logprob to confidence (recheck calculation as this is a rough approximation)
                        confidence = max(0.1, min(1.0, (logprob + 3.0) / 3.0))
                    elif 'confidence' in segment:
                        confidence = float(segment.get('confidence', 0.8))
                    
                    confidence = max(0.1, min(1.0, confidence))
                    
                    # ensure end time is after start time
                    if end_time <= start_time:
                        words = len(text.split())
                        estimated_duration = max(1.0, words / 2.5) 
                        end_time = start_time + estimated_duration
                        logger.debug(f"Estimated duration for segment {i}: {estimated_duration:.2f}s")
                    
                    # add the segment to the list
                    segments.append(TranscriptionSegment(
                        start=start_time,
                        end=end_time,
                        text=text,
                        confidence=confidence
                    ))
                    
                    logger.debug(f"Segment {i}: {start_time:.2f}-{end_time:.2f}s, confidence: {confidence:.2f}")
            
            # handle text-only response 
            elif 'text' in result and result['text'].strip():
                logger.info("Processing text-only transcription (no segments)")
                full_text = result['text'].strip()
                
                # split text into reasonable chunks for subtitle display
                sentences = self._split_text_into_sentences(full_text)
                
                # estimate total duration based on word count
                words = len(full_text.split())
                estimated_total_duration = max(5.0, words / 2.5)  # 2.5 words per second
                
                current_time = 0.0
                for i, sentence in enumerate(sentences):
                    sentence_words = len(sentence.split())
                    sentence_duration = max(1.0, sentence_words / 2.5)
                    
                    segments.append(TranscriptionSegment(
                        start=current_time,
                        end=current_time + sentence_duration,
                        text=sentence,
                        confidence=0.8
                    ))
                    
                    current_time += sentence_duration
                    logger.debug(f"Text segment {i}: {sentence_words} words, {sentence_duration:.2f}s")
            
            # calculate overall confidence
            if segments:
                overall_confidence = sum(seg.confidence for seg in segments) / len(segments)
            else:
                overall_confidence = 0.0
            
            # clean the final text
            final_text = self._clean_transcription_text(result.get('text', '').strip())
            detected_language = result.get('language', expected_language or 'en')
            
            logger.info(f"Conversion completed:")
            logger.info(f"  - Final segments: {len(segments)}")
            logger.info(f"  - Final text length: {len(final_text)}")
            logger.info(f"  - Overall confidence: {overall_confidence:.2f}")
            
            return TranscriptionResult(
                text=final_text,
                segments=segments,
                detected_language=detected_language,
                confidence=overall_confidence
            )
        
        #error handling
        except Exception as e:
            logger.error(f"Error converting Groq result: {str(e)}")
            return TranscriptionResult(
                text=result.get('text', ''),
                segments=[],
                detected_language='en',
                confidence=0.0
            )
    
    #current method for real obvious hallucination detection (not sure if this is needed or the most effective)
    def _is_likely_hallucination(self, text: str, expected_language: Optional[str] = None) -> bool:
        """Detect potential hallucinations using very conservative heuristics"""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip().lower()
        
        # only catch the most obvious hallucinations - be very conservative
        hallucination_indicators = [
            # single meaningless characters or very short nonsense
            len(text) <= 2 and not text.isalnum(),
            # only flag extremely obvious repeated patterns
            len(text) > 20 and len(set(text.replace(' ', ''))) == 1, 
        ]
        
        return any(hallucination_indicators)
    
    #another method for error handling 
    def _contains_multiple_scripts(self, text: str) -> bool:
        """check if text contains multiple writing scripts (indicating mixed languages)"""
        # simple check for mixed scripts - only flag obvious cases
        has_latin = any('a' <= c <= 'z' or 'A' <= c <= 'Z' for c in text)
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        has_arabic = any('\u0600' <= c <= '\u06ff' for c in text)
        has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in text)
        
        script_count = sum([has_latin, has_chinese, has_arabic, has_cyrillic])
        return script_count > 1
    
    def _clean_transcription_text(self, text: str) -> str:
        """Clean transcription text of common artifacts"""
        if not text:
            return ""
        
        # remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _split_text_into_sentences(self, text: str) -> List[str]:
        """split text into sentences for better subtitle timing"""
        import re
        
        # split on sentence endings
        sentences = re.split(r'[.!?]+', text)
        
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        # fallback: split on commas if no sentences found
        if not cleaned_sentences:
            if ',' in text:
                parts = text.split(',')
                cleaned_sentences = [part.strip() for part in parts if part.strip()]
            else:
                # last resort: split into chunks of words
                words = text.split()
                chunk_size = 10 
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i + chunk_size])
                    if chunk.strip():
                        cleaned_sentences.append(chunk.strip())
        
        return cleaned_sentences or [text]
    
    async def detect_language(self, audio_path: str) -> str:
        """detect the language of the audio file when the user does not specify"""
        try:
            logger.info(f"Detecting language for audio: {audio_path}")
            
            # transcribe a short sample for language detection
            transcription_result = await self._transcribe_sample(audio_path, max_duration=30)
            
            if transcription_result.detected_language:
                detected_lang = get_language_code(transcription_result.detected_language)
                logger.info(f"Language detected: {detected_lang}")
                return detected_lang
            
            logger.warning("No language detected, defaulting to English")
            return "en"
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return "en"
    
    #transcribe short sample to detect language
    async def _transcribe_sample(self, audio_path: str, max_duration: int = 30) -> TranscriptionResult:
        """transcribe a short sample for language detection"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            #use ffmpeg to extract a short sample for language detection
            import subprocess
            cmd = [
                'ffmpeg', '-i', audio_path, 
                '-ss', '0', '-t', str(max_duration),
                '-ar', '16000', '-ac', '1',
                '-y', temp_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            result = await self.transcribe_audio(temp_path)
            
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing sample: {str(e)}")
            raise
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", 
            "ar", "hi", "th", "vi", "nl", "sv", "no", "da", "fi", "pl",
            "tr", "cs", "hu", "ro", "bg", "hr", "sk", "sl", "et", "lv",
            "lt", "uk", "he", "fa", "ur", "bn", "ta", "te", "ml", "kn",
            "gu", "mr", "ne", "si", "my", "km", "lo", "ka", "am", "sw",
            "zu", "af", "ms", "tl", "id"
        ]
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current model"""
        model_info = {
            "whisper-large-v3": {
                "name": "Whisper Large v3",
                "description": "Most accurate, supports 99+ languages",
                "speed": "Medium",
                "accuracy": "Highest"
            },
            "whisper-large-v3-turbo": {
                "name": "Whisper Large v3 Turbo", 
                "description": "Faster version of Large v3",
                "speed": "Fast",
                "accuracy": "High"
            },
            "distil-whisper-large-v3-en": {
                "name": "Distil-Whisper Large v3 EN",
                "description": "English-only, very fast",
                "speed": "Very Fast",
                "accuracy": "High (English only)"
            }
        }
        
        return model_info.get(self.model, {
            "name": self.model,
            "description": "Unknown model",
            "speed": "Unknown",
            "accuracy": "Unknown"
        }) 