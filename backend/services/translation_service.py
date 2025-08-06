import asyncio
import logging
from typing import List, Optional, Dict
from groq import Groq
import json
import re

from models.requests import TranslationResult, TranscriptionSegment
from utils.config import get_settings, get_language_name, get_language_code, validate_groq_key

logger = logging.getLogger(__name__)

class TranslationService:
    """
    service for translating text
    """
    
    def __init__(self):
        self.settings = get_settings()
        validate_groq_key()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.model = self.settings.groq_model
    
    #main public interface for translating text (asynchronous method)
    #translates a given text from a source language to a target language
    #returns a TranslationResults
    async def translate_text(self, text: str, source_language: str, target_language: str, 
                           context: Optional[str] = None) -> TranslationResult:
        """
        translate text from source to target language
        """
        try:
            logger.info(f"Translating text from {source_language} to {target_language}")
            
            # skip translation if source and target are the same
            if source_language.lower() == target_language.lower():
                return TranslationResult(
                    translated_text=text,
                    source_language=source_language,
                    target_language=target_language,
                    confidence=1.0
                )
            
            # get language names for better context
            source_lang_name = get_language_name(source_language)
            target_lang_name = get_language_name(target_language)
            
            prompt = self._create_translation_prompt(
                text, source_lang_name, target_lang_name, context
            )
            
            loop = asyncio.get_event_loop()
            translated_text = await loop.run_in_executor(
                None, 
                self._translate_with_groq, 
                prompt
            )
            
            # post-process the translation
            translated_text = self._post_process_translation(translated_text)
            
            logger.info(f"Translation completed. Original: {len(text)} chars, Translated: {len(translated_text)} chars")
            
            return TranslationResult(
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.9  
            )
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise Exception(f"Translation failed: {str(e)}")
    
    #translates multiple transcription segments with TranscriptionSegment objects
    #returns a list of translated segments
    async def translate_segments(self, segments: List[TranscriptionSegment], 
                               source_language: str, target_language: str) -> List[TranscriptionSegment]:
        """
        translate multiple segments with context awareness
        """
        try:
            logger.info(f"Translating {len(segments)} segments")
            
            # skip translation if source and target are the same
            if source_language.lower() == target_language.lower():
                return segments
            
            batch_size = 10
            translated_segments = []
            
            for i in range(0, len(segments), batch_size):
                batch = segments[i:i + batch_size]
                
                batch_text = self._create_batch_text(batch)
                
                # translate the batch
                translated_batch = await self.translate_text(
                    batch_text, 
                    source_language, 
                    target_language,
                    context="This is a batch of subtitle segments from a video. Maintain natural flow and context."
                )
                
                # parse the translated batch back to segments
                translated_batch_segments = self._parse_batch_translation(
                    translated_batch.translated_text, batch
                )
                
                translated_segments.extend(translated_batch_segments)
            
            logger.info(f"Segment translation completed: {len(translated_segments)} segments")
            
            return translated_segments
            
        except Exception as e:
            logger.error(f"Segment translation error: {str(e)}")
            raise Exception(f"Segment translation failed: {str(e)}")
    
    #creates a prompt for the translation
    def _create_translation_prompt(self, text: str, source_lang: str, target_lang: str, 
                                 context: Optional[str] = None) -> str:
        """
        Create an optimized prompt for Groq translation
        """
        prompt = f"""You are a professional translator specializing in subtitle translation for videos. 

Task: Translate the following text from {source_lang} to {target_lang}.

Instructions:
1. Maintain natural flow and readability for subtitles
2. Keep cultural context and nuances
3. Use appropriate subtitle conventions for {target_lang}
4. Preserve timing and pacing suitable for spoken dialogue
5. Handle names, places, and technical terms appropriately
6. Keep similar length when possible for subtitle display
7. Add the approriate substitutes for interjections. 
8. ENSURE THAT THE ENTIRE TEXT IS TRANSLATED TO THE TARGET LANGUAGE.

{f"Context: {context}" if context else ""}

Source text ({source_lang}):
{text}

Translated text ({target_lang}):"""
        
        return prompt
    
    #actual translation method that calls the groq api
    def _translate_with_groq(self, prompt: str) -> str:
        """
        Perform the actual translation using Groq 
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  
                max_tokens=2000,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Groq translation error: {str(e)}")
            raise
    
    #post-process the translation to clean up common issues
    def _post_process_translation(self, translated_text: str) -> str:
        """
        Post-process the translated text to clean up common issues
        """
        prefixes_to_remove = [
            "Translated text:",
            "Translation:",
            "Here's the translation:",
            "The translation is:",
            "In English:",
            "In Spanish:",
            "In French:",
            "In German:",
            "In Italian:",
            "In Portuguese:",
            "In Russian:",
            "In Japanese:",
            "In Korean:",
            "In Chinese:",
            "In Arabic:",
            "In Hindi:",
        ]
        
        for prefix in prefixes_to_remove:
            if translated_text.lower().startswith(prefix.lower()):
                translated_text = translated_text[len(prefix):].strip()
        
        if translated_text.startswith('"') and translated_text.endswith('"'):
            translated_text = translated_text[1:-1]
        
        if translated_text.startswith("'") and translated_text.endswith("'"):
            translated_text = translated_text[1:-1]
        
        return translated_text.strip()
    
    def _create_batch_text(self, segments: List[TranscriptionSegment]) -> str:
        """
        create a batch text from segments with markers for parsing
        """
        batch_lines = []
        for i, segment in enumerate(segments):
            batch_lines.append(f"[{i}] {segment.text}")
        
        return "\n".join(batch_lines)
    
    def _parse_batch_translation(self, translated_text: str, 
                               original_segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        """
        parse the translated batch back to individual segments
        """
        try:
            lines = translated_text.strip().split('\n')
            translated_segments = []
            
            segment_map = {}
            for line in lines:
                line = line.strip()
                if line and line.startswith('[') and ']' in line:
                    # Extract segment index and text
                    marker_end = line.find(']')
                    if marker_end > 0:
                        try:
                            index = int(line[1:marker_end])
                            text = line[marker_end + 1:].strip()
                            segment_map[index] = text
                        except ValueError:
                            continue
            
            for i, original_segment in enumerate(original_segments):
                translated_text = segment_map.get(i, original_segment.text)
                
                translated_segments.append(TranscriptionSegment(
                    start=original_segment.start,
                    end=original_segment.end,
                    text=translated_text,
                    confidence=original_segment.confidence
                ))
            
            return translated_segments
            
        except Exception as e:
            logger.error(f"Error parsing batch translation: {str(e)}")
            return original_segments
    
    async def detect_language_groq(self, text: str) -> str:
        """
        use groq to detect the language of text
        """
        try:
            prompt = f"""Detect the language of the following text and respond with only the language code (e.g., 'en' for English, 'es' for Spanish, 'fr' for French, etc.).

Text: {text[:500]}

Language code:"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._translate_with_groq, 
                prompt
            )
            
            # extract language code from response
            detected_lang = response.strip().lower()
            
            # validate against supported languages
            if detected_lang in self.settings.supported_languages:
                return detected_lang
            
            # try to match against language names
            for code, name in self.settings.supported_languages.items():
                if name.lower() in detected_lang.lower():
                    return code
            
            logger.warning(f"Unknown language detected: {detected_lang}, defaulting to 'en'")
            return "en"
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return "en"
    
    async def improve_translation_quality(self, original_text: str, translated_text: str,
                                        source_language: str, target_language: str) -> str:
        """
        use groq to improve translation quality by reviewing and refining
        """
        try:
            source_lang_name = get_language_name(source_language)
            target_lang_name = get_language_name(target_language)
            
            prompt = f"""Review and improve the following translation for subtitle display:

You are a professional subtitle translator. Your task is to improve subtitle translations with high accuracy and natural fluency.

Original ({source_lang_name}): "{original_text}"
Current Translation ({target_lang_name}): "{translated_text}"

Guidelines:
1. Return **only the improved subtitle translation**, nothing else (no explanations or reasoning).
2. If the original text is background music, sound effects, or irrelevant (e.g., intro/outro credits, logos, gibberish), return an **empty string** "" to omit it from subtitles.
3. If a character repeats a word for emphasis (e.g., "no no no"), keep it natural but **limit repetition** to 2–3 times max unless it’s critical to context.
4. Keep translation concise and natural for subtitle display. Avoid overly long sentences.
5. Do not insert random characters, numbers, or non-speech text.
6. ENSURE THAT THE ENTIRE TEXT IS TRANSLATED TO THE TARGET LANGUAGE.

Improved translation:"""
            
            loop = asyncio.get_event_loop()
            improved_translation = await loop.run_in_executor(
                None, 
                self._translate_with_groq, 
                prompt
            )
            
            return self._post_process_translation(improved_translation)
            
        except Exception as e:
            logger.error(f"Translation improvement error: {str(e)}")
            return translated_text 
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages for translation
        """
        return self.settings.supported_languages