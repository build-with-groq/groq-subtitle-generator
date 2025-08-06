import os
import asyncio
import logging
from typing import List, Optional
import pysrt
import webvtt
from datetime import timedelta

from models.requests import TranscriptionSegment, TranscriptionResult, SubtitleEntry
from utils.config import get_settings
from utils.file_utils import ensure_directory_exists, get_safe_filename

logger = logging.getLogger(__name__)

class SubtitleService:
    """
    create subtitle files from transcription segments
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def create_subtitle_file(self, transcription_result: TranscriptionResult, 
                                 job_id: str, format: str = "srt") -> str:
        """
        create a subtitle file from transcription result
        """
        try:
            logger.info(f"Creating {format.upper()} subtitle file for job {job_id}")
            # optimize segments for subtitle display
            optimized_segments = self._optimize_segments_for_subtitles(
                transcription_result.segments
            )
            
            # generate subtitle file based on format
            if format.lower() == "srt":
                subtitle_path = await self._create_srt_file(optimized_segments, job_id)
            elif format.lower() == "vtt":
                subtitle_path = await self._create_vtt_file(optimized_segments, job_id)
            else:
                raise ValueError(f"Unsupported subtitle format: {format}")
            
            logger.info(f"Subtitle file created: {subtitle_path}")
            return subtitle_path
            
        except Exception as e:
            logger.error(f"Error creating subtitle file: {str(e)}")
            raise Exception(f"Subtitle creation failed: {str(e)}")
    
    async def _create_srt_file(self, segments: List[TranscriptionSegment], job_id: str) -> str:
        """
        create SRT format subtitle file
        """
        try:
            # generate output path
            subtitle_path = get_safe_filename(
                f"subtitles_{job_id}", 
                "srt", 
                f"{self.settings.temp_dir}/subtitles"
            )
            
            # create SRT subtitle file
            srt_subs = pysrt.SubRipFile()
            
            for i, segment in enumerate(segments, 1):
                # convert seconds to SRT time format
                start_time = self._seconds_to_srt_time(segment.start)
                end_time = self._seconds_to_srt_time(segment.end)
                
                # create subtitle item
                subtitle_item = pysrt.SubRipItem(
                    index=i,
                    start=start_time,
                    end=end_time,
                    text=segment.text
                )
                
                srt_subs.append(subtitle_item)
            
            # save to file
            srt_subs.save(subtitle_path, encoding='utf-8')
            
            return subtitle_path
            
        except Exception as e:
            logger.error(f"Error creating SRT file: {str(e)}")
            raise
    
    async def _create_vtt_file(self, segments: List[TranscriptionSegment], job_id: str) -> str:
        """
        Create VTT format subtitle file
        """
        try:
            # generate output path
            subtitle_path = get_safe_filename(
                f"subtitles_{job_id}", 
                "vtt", 
                f"{self.settings.temp_dir}/subtitles"
            )
            
            # create VTT subtitle file
            vtt_subs = webvtt.WebVTT()
            
            for segment in segments:
                # convert seconds to VTT time format
                start_time = self._seconds_to_vtt_time(segment.start)
                end_time = self._seconds_to_vtt_time(segment.end)
                
                # create caption
                caption = webvtt.Caption(
                    start=start_time,
                    end=end_time,
                    text=segment.text
                )
                
                vtt_subs.captions.append(caption)
            
            # save to file
            vtt_subs.save(subtitle_path)
            
            return subtitle_path
            
        except Exception as e:
            logger.error(f"Error creating VTT file: {str(e)}")
            raise
    
    def _optimize_segments_for_subtitles(self, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        """
        optimize segments for subtitle display
        """
        optimized_segments = []
        
        for segment in segments:
            # skip empty segments
            if not segment.text.strip():
                continue
            
            duration = segment.end - segment.start
            
            min_duration = max(1.0, len(segment.text) * 0.05)  # 50ms per character
            
            if duration < min_duration:
                segment.end = segment.start + min_duration
            
            max_duration = 7.0
            if duration > max_duration:
                # split long segments
                split_segments = self._split_long_segment(segment, max_duration)
                optimized_segments.extend(split_segments)
            else:
                optimized_segments.append(segment)
        
        # ensure no overlapping segments
        return self._remove_overlaps(optimized_segments)
    
    def _split_long_segment(self, segment: TranscriptionSegment, max_duration: float) -> List[TranscriptionSegment]:
        """
        split a long segment into multiple shorter ones
        """
        segments = []
        text = segment.text
        words = text.split()
        
        if len(words) <= 1:
            return [segment]
        
        # split into roughly equal parts
        duration = segment.end - segment.start
        num_parts = int(duration / max_duration) + 1
        words_per_part = len(words) // num_parts
        
        current_start = segment.start
        for i in range(num_parts):
            start_idx = i * words_per_part
            end_idx = (i + 1) * words_per_part if i < num_parts - 1 else len(words)
            
            if start_idx >= len(words):
                break
            
            part_text = ' '.join(words[start_idx:end_idx])
            part_duration = (duration / num_parts)
            part_end = current_start + part_duration
            
            segments.append(TranscriptionSegment(
                start=current_start,
                end=part_end,
                text=part_text,
                confidence=segment.confidence
            ))
            
            current_start = part_end
        
        return segments
    
    def _remove_overlaps(self, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        """
        remove overlapping segments
        """
        if not segments:
            return segments
        
        # sort by start time
        segments.sort(key=lambda x: x.start)
        
        cleaned_segments = []
        for segment in segments:
            if not cleaned_segments:
                cleaned_segments.append(segment)
                continue
            
            last_segment = cleaned_segments[-1]
            
            # check for overlap
            if segment.start < last_segment.end:
                # adjust start time to avoid overlap
                gap = 0.1
                segment.start = last_segment.end + gap
                
                # ensure end time is still after start time
                if segment.end <= segment.start:
                    segment.end = segment.start + 1.0
            
            cleaned_segments.append(segment)
        
        return cleaned_segments
    
    def _seconds_to_srt_time(self, seconds: float) -> pysrt.SubRipTime:
        """
        convert seconds to SRT time format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return pysrt.SubRipTime(hours, minutes, secs, milliseconds)
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """
        convert seconds to VTT time format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def validate_subtitle_file(self, file_path: str) -> bool:
        """
        validate a subtitle file
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.srt':
                # try to parse SRT file
                subs = pysrt.open(file_path)
                return len(subs) > 0
            elif file_extension == '.vtt':
                # try to parse VTT file
                vtt = webvtt.read(file_path)
                return len(vtt.captions) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating subtitle file: {str(e)}")
            return False
    
    def get_subtitle_stats(self, file_path: str) -> dict:
        """
        get statistics about a subtitle file
        """
        try:
            if not os.path.exists(file_path):
                return {}
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.srt':
                subs = pysrt.open(file_path)
                total_duration = 0
                total_chars = 0
                
                for sub in subs:
                    duration = (sub.end - sub.start).total_seconds()
                    total_duration += duration
                    total_chars += len(sub.text)
                
                return {
                    'format': 'SRT',
                    'subtitle_count': len(subs),
                    'total_duration': total_duration,
                    'total_characters': total_chars,
                    'average_duration': total_duration / len(subs) if subs else 0,
                    'average_characters': total_chars / len(subs) if subs else 0
                }
            
            elif file_extension == '.vtt':
                vtt = webvtt.read(file_path)
                total_duration = 0
                total_chars = 0
                
                for caption in vtt.captions:
                    start_seconds = self._vtt_time_to_seconds(caption.start)
                    end_seconds = self._vtt_time_to_seconds(caption.end)
                    duration = end_seconds - start_seconds
                    total_duration += duration
                    total_chars += len(caption.text)
                
                return {
                    'format': 'VTT',
                    'subtitle_count': len(vtt.captions),
                    'total_duration': total_duration,
                    'total_characters': total_chars,
                    'average_duration': total_duration / len(vtt.captions) if vtt.captions else 0,
                    'average_characters': total_chars / len(vtt.captions) if vtt.captions else 0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"error getting subtitle stats: {str(e)}")
            return {}
    
    def _vtt_time_to_seconds(self, vtt_time: str) -> float:
        """
        convert VTT time format to seconds
        """
        try:
            parts = vtt_time.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception:
            return 0.0
    
    def convert_subtitle_format(self, input_path: str, output_format: str, job_id: str) -> str:
        """
        convert subtitle file from one format to another
        """
        try:
            input_extension = os.path.splitext(input_path)[1].lower()
            
            # generate output path
            output_path = get_safe_filename(
                f"converted_{job_id}", 
                output_format, 
                f"{self.settings.temp_dir}/subtitles"
            )
            
            if input_extension == '.srt' and output_format == 'vtt':
                # convert SRT to VTT
                srt_subs = pysrt.open(input_path)
                vtt_subs = webvtt.WebVTT()
                
                for sub in srt_subs:
                    start_time = self._srt_time_to_vtt_time(sub.start)
                    end_time = self._srt_time_to_vtt_time(sub.end)
                    
                    caption = webvtt.Caption(
                        start=start_time,
                        end=end_time,
                        text=sub.text
                    )
                    
                    vtt_subs.captions.append(caption)
                
                vtt_subs.save(output_path)
                
            elif input_extension == '.vtt' and output_format == 'srt':
                # convert VTT to SRT
                vtt_subs = webvtt.read(input_path)
                srt_subs = pysrt.SubRipFile()
                
                for i, caption in enumerate(vtt_subs.captions, 1):
                    start_time = self._vtt_time_to_srt_time(caption.start)
                    end_time = self._vtt_time_to_srt_time(caption.end)
                    
                    subtitle_item = pysrt.SubRipItem(
                        index=i,
                        start=start_time,
                        end=end_time,
                        text=caption.text
                    )
                    
                    srt_subs.append(subtitle_item)
                
                srt_subs.save(output_path, encoding='utf-8')
            
            else:
                raise ValueError(f"unsupported conversion: {input_extension} to {output_format}")
            
            logger.info(f"subtitle converted from {input_extension} to {output_format}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"error converting subtitle format: {str(e)}")
            raise
    
    def _srt_time_to_vtt_time(self, srt_time: pysrt.SubRipTime) -> str:
        """
        convert SRT time to VTT time format
        """
        total_seconds = srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000
        return self._seconds_to_vtt_time(total_seconds)
    
    def _vtt_time_to_srt_time(self, vtt_time: str) -> pysrt.SubRipTime:
        """
        convert VTT time to SRT time format
        """
        seconds = self._vtt_time_to_seconds(vtt_time)
        return self._seconds_to_srt_time(seconds) 
    
    async def generate_srt_content(self, transcription_result: TranscriptionResult) -> str:
        """
        generate SRT subtitle content as a string without saving to disk
        """
        try:
            logger.info("generating SRT content in memory")
            
            optimized_segments = self._optimize_segments_for_subtitles(
                transcription_result.segments
            )
            
            srt_lines = []
            
            for i, segment in enumerate(optimized_segments, 1):
                start_time = self._seconds_to_srt_time_string(segment.start)
                end_time = self._seconds_to_srt_time_string(segment.end)

                srt_lines.append(str(i))
                srt_lines.append(f"{start_time} --> {end_time}")
                srt_lines.append(segment.text)
                srt_lines.append("") 
            
            srt_content = "\n".join(srt_lines)
            logger.info(f"generated SRT content with {len(optimized_segments)} segments")
            
            return srt_content
            
        except Exception as e:
            logger.error(f"error generating SRT content: {str(e)}")
            raise Exception(f"SRT generation failed: {str(e)}")
    
    def _seconds_to_srt_time_string(self, seconds: float) -> str:
        """
        convert seconds to SRT time format string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}" 