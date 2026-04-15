"""
Service for extracting video clips from videos.
"""
import asyncio
import logging
import os
import tempfile
import json
import ast
from typing import Dict, Any, List
import uuid
from pydantic import AnyUrl

import ffmpeg
from app.services.speaches.stt_client import transcribe_audio
from app.utils.media import download_media_file, get_media_info
from app.services.s3.s3 import s3_service
from app.services.job_queue import job_queue
from app.services.ai.unified_ai_service import unified_ai_service
from app.models import JobStatus
from app.models import VideoClipsResult
from app.utils.logging import get_logger

# Use enhanced logging
logger = get_logger(module="clips_service", component="video_processing")


class VideoClipsService:
    """Service for extracting video clips."""

    def __init__(self):
        self.unified_service = unified_ai_service
    
    async def process_clips_job(self, job_id: str, params: Dict[str, Any]) -> dict[str, Any]:
        """
        Process a video clips extraction job.
        
        Args:
            job_id: The job identifier
            params: Job parameters containing video_url, segments, output_format, quality
        """
        try:
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=0)
            
            video_url = params["video_url"]
            output_format = params.get("output_format", "mp4")
            quality = params.get("quality", "medium")
            
            # Convert Pydantic URL objects to strings
            video_url = str(video_url)
            
            # Download the video file
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
            video_path, _ = await download_media_file(video_url, job_id)
            
            try:
                # Get video metadata
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=15)
                video_info = await get_media_info(video_path)
                video_duration = video_info.get("duration", 0)
                
                # Determine if using manual segments or AI query
                if "segments" in params:
                    segments = params["segments"]
                    logger.info(f"Starting manual clips extraction for job {job_id} with {len(segments)} segments")
                    valid_segments = self._validate_segments(segments, video_duration)
                else:
                    ai_query = params["ai_query"]
                    max_clips = params.get("max_clips", 5)
                    logger.info(f"Starting AI clips extraction for job {job_id} with query: '{ai_query}'")
                    
                    # AI-powered segment detection
                    await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=20)
                    valid_segments = await self._find_ai_segments(video_path, ai_query, max_clips, video_duration, job_id)
                
                if not valid_segments:
                    raise ValueError("No valid segments found for clip extraction")
                
                # Generate clips
                progress_start = 50 if "ai_query" in params else 20
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=progress_start)
                clip_urls = await self._extract_clips(
                    video_path, valid_segments, output_format, quality, job_id
                )
                
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=90)
                
                # Calculate total duration
                total_duration = sum(
                    segment["end"] - segment["start"] 
                    for segment in valid_segments
                )
                
                # Create result (convert string URLs to AnyUrl)
                clip_anyurls = [AnyUrl(url) for url in clip_urls]
                result = VideoClipsResult(
                    clip_urls=clip_anyurls,
                    segments_processed=len(clip_urls),
                    total_duration=total_duration
                )
                
                await job_queue.update_job_status(
                    job_id, 
                    JobStatus.COMPLETED, 
                    result=result.model_dump(),
                    progress=100
                )
                
                logger.info(f"Successfully extracted {len(clip_urls)} clips for job {job_id}")
                
                return result.model_dump()
                
            finally:
                # Clean up video file
                if os.path.exists(video_path):
                    os.unlink(video_path)
                    
        except Exception as e:
            logger.error(f"Error processing clips job {job_id}: {str(e)}")
            await job_queue.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                error=str(e)
            )
            raise e
    
    def _validate_segments(self, segments: List[Dict[str, Any]], video_duration: float) -> List[Dict[str, Any]]:
        """
        Validate and adjust segments against video duration.
        
        Args:
            segments: List of segment dictionaries
            video_duration: Total video duration in seconds
            
        Returns:
            List of valid segment dictionaries
        """
        valid_segments = []
        
        for i, segment in enumerate(segments):
            start = segment["start"]
            end = segment["end"]
            name = segment.get("name", f"clip_{i+1}")
            
            # Validate segment times
            if start < 0:
                start = 0
            if end > video_duration:
                end = video_duration
            if start >= end:
                logger.warning(f"Skipping invalid segment {i}: start >= end after adjustments")
                continue
                
            valid_segments.append({
                "start": start,
                "end": end,
                "name": name,
                "duration": end - start
            })
        
        return valid_segments
    
    def _get_quality_settings(self, quality: str) -> Dict[str, Any]:
        """
        Get FFmpeg quality settings based on quality preset.
        
        Args:
            quality: Quality preset (low, medium, high)
            
        Returns:
            Dictionary of FFmpeg options
        """
        settings = {
            "low": {
                "crf": 28,
                "preset": "fast",
                "scale": None  # Keep original resolution
            },
            "medium": {
                "crf": 23,
                "preset": "medium",
                "scale": None
            },
            "high": {
                "crf": 18,
                "preset": "slow",
                "scale": None
            }
        }
        
        return settings.get(quality, settings["medium"])
    
    async def _extract_clips(
        self, 
        video_path: str, 
        segments: List[Dict[str, Any]], 
        output_format: str,
        quality: str,
        job_id: str
    ) -> List[str]:
        """
        Extract video clips for each segment.
        
        Args:
            video_path: Path to the video file
            segments: List of valid segments
            output_format: Output video format
            quality: Quality preset
            job_id: Job identifier for unique naming
            
        Returns:
            List of S3 URLs for the generated clips
        """
        clip_urls = []
        temp_dir = tempfile.mkdtemp()
        quality_settings = self._get_quality_settings(quality)
        
        try:
            for i, segment in enumerate(segments):
                # Generate unique filename
                name = segment["name"] or f"clip_{i+1}"
                # Sanitize filename
                safe_name = "".join(c for c in name if c.isalnum() or c in "._-")[:50]
                filename = f"{safe_name}_{job_id}_{i:03d}.{output_format}"
                temp_clip_path = os.path.join(temp_dir, filename)
                
                try:
                    # Extract clip using ffmpeg
                    input_stream = ffmpeg.input(
                        video_path, 
                        ss=segment["start"],
                        t=segment["duration"]
                    )
                    
                    # Apply quality settings
                    output_args = {
                        "c:v": "libx264",
                        "crf": quality_settings["crf"],
                        "preset": quality_settings["preset"],
                        "c:a": "aac"
                    }
                    
                    # Apply scaling if specified
                    if quality_settings.get("scale"):
                        input_stream = ffmpeg.filter(input_stream, "scale", quality_settings["scale"])
                    
                    output_stream = ffmpeg.output(
                        input_stream,
                        temp_clip_path,
                        **output_args
                    )
                    
                    # Run ffmpeg command
                    process = await asyncio.create_subprocess_exec(
                        *ffmpeg.compile(output_stream, overwrite_output=True),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        logger.error(f"FFmpeg error for segment {i}: {stderr.decode()}")
                        continue
                    
                    # Upload to S3
                    if os.path.exists(temp_clip_path) and os.path.getsize(temp_clip_path) > 0:
                        s3_key = f"video_clips/{job_id}/{filename}"
                        s3_url = await s3_service.upload_file(temp_clip_path, s3_key)
                        clip_urls.append(s3_url)
                        
                        logger.debug(f"Generated clip {i+1}/{len(segments)}: {name} ({segment['duration']:.2f}s)")
                    else:
                        logger.warning(f"Failed to generate clip for segment {i}: {name}")
                        
                except Exception as e:
                    logger.error(f"Error generating clip for segment {i}: {str(e)}")
                    continue
                finally:
                    # Clean up temp clip file
                    if os.path.exists(temp_clip_path):
                        os.unlink(temp_clip_path)
                
                # Update progress
                progress = 20 + int((i + 1) / len(segments) * 70)
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=progress)
            
            return clip_urls
            
        finally:
            # Clean up temp directory
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or other error

    async def _find_ai_segments(
        self, 
        video_path: str, 
        query: str, 
        max_clips: int, 
        video_duration: float,
        job_id: str
    ) -> List[Dict[str, Any]]:
        """
        Use AI to find relevant segments based on natural language query.
        
        Args:
            video_path: Path to the video file
            query: Natural language query describing desired clips
            max_clips: Maximum number of clips to return
            video_duration: Total video duration
            job_id: Job identifier for progress updates
            
        Returns:
            List of segment dictionaries with start, end, name, and duration
        """
        try:
            # Extract audio for transcription
            await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=25)
            audio_path = await self._extract_audio_for_transcription(video_path)
            
            try:
                # Transcribe audio with timestamps
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
                transcription = await self._transcribe_video_with_timestamps(audio_path)
                
                if not transcription:
                    logger.warning(f"No transcription found for video in job {job_id}")
                    return []
                
                # Use AI to find relevant segments
                await job_queue.update_job_status(job_id, JobStatus.PROCESSING, progress=40)
                relevant_segments = await self._get_relevant_segments_with_ai(
                    transcription, query, max_clips
                )
                
                # Validate segments against video duration
                valid_segments = []
                for i, segment in enumerate(relevant_segments):
                    start = max(0, segment.get("start", 0))
                    end = min(video_duration, segment.get("end", start + 30))
                    
                    if start < end and (end - start) >= 1.0:  # At least 1 second
                        valid_segments.append({
                            "start": start,
                            "end": end,
                            "name": f"ai_clip_{i+1}",
                            "duration": end - start
                        })
                
                logger.info(f"Found {len(valid_segments)} relevant segments for query: '{query}'")
                return valid_segments
                
            finally:
                # Clean up audio file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
                    
        except Exception as e:
            logger.error(f"Error in AI segment detection: {str(e)}")
            return []

    async def _extract_audio_for_transcription(self, video_path: str) -> str:
        """Extract audio from video for transcription."""
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "temp_audio.wav")
        
        # Use FFmpeg to extract audio
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", video_path, "-ar", "16000", "-ac", "1", 
            "-b:a", "64k", "-f", "wav", audio_path, "-y",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to extract audio: {stderr.decode()}")
            
        return audio_path

    async def _transcribe_video_with_timestamps(self, audio_path: str) -> List[Dict[str, Any]]:
        """Transcribe audio using Speaches sidecar with precise timestamps."""
        try:
            segments, info = await transcribe_audio(
                file_path=audio_path,
                model="Systran/faster-whisper-base",
                language="en",
            )

            # Convert to our format
            transcription = []
            for segment in segments:
                transcription.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })

            logger.info(f"Transcribed audio with {len(transcription)} segments")
            return transcription

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return []

    async def _get_relevant_segments_with_ai(
        self,
        transcription: List[Dict[str, Any]],
        query: str,
        max_clips: int
    ) -> List[Dict[str, Any]]:
        """Use AI to find relevant segments based on query."""
        try:
            # Format transcription for AI
            transcript_text = "\n".join([
                f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
                for seg in transcription
            ])

            system_prompt = """You are an expert video editor who can read video transcripts and perform video editing. Given a transcript with segments, your task is to identify all the conversations related to a user query. Follow these guidelines when choosing conversations. A group of continuous segments in the transcript is a conversation.

Guidelines:
1. The conversation should be relevant to the user query. The conversation should include more than one segment to provide context and continuity.
2. Include all the before and after segments needed in a conversation to make it complete.
3. The conversation should not cut off in the middle of a sentence or idea.
4. Choose multiple conversations from the transcript that are relevant to the user query.
5. Match the start and end time of the conversations using the segment timestamps from the transcript.
6. The conversations should be a direct part of the video and should not be out of context.

Output format: { "conversations": [{"start": s1, "end": e1}, {"start": s2, "end": e2}] }

Return only valid JSON in the specified format."""

            user_content = f"""Transcript:
{transcript_text}

User query: {query}
Maximum clips to return: {max_clips}

Find the most relevant conversations and return them in JSON format."""

            # Make the API call using unified AI service
            response = await self.unified_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                provider="auto",
                temperature=0.1,
                max_tokens=1024
            )

            content = response.get('content')
            provider_used = response.get('provider_used', 'unknown')
            model_used = response.get('model_used', 'unknown')
            logger.info(f"AI analysis completed using {provider_used} model {model_used}")

            # Parse the AI response
            if content is None:
                logger.warning("Received None content from AI response")
                return []

            try:
                parsed_response = ast.literal_eval(content)
                return parsed_response.get("conversations", [])
            except (ValueError, SyntaxError):
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                    return parsed_response.get("conversations", [])

        except Exception as e:
            logger.error(f"Error getting AI segments: {str(e)}")

        return []


# Global service instance
video_clips_service = VideoClipsService()