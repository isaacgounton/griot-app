"""
FFmpeg Composer Service - Compose and execute complex FFmpeg commands from JSON configuration.
"""
import os
import uuid
import asyncio
import logging
import subprocess
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import tempfile

from app.models import (
    FFmpegComposeRequest, 
    FFmpegComposeResult, 
    FFmpegOutputResult,
    FFmpegOption,
    FFmpegInput,
    FFmpegFilter,
    FFmpegOutput
)
from app.services.s3.s3 import s3_service
from app.utils.download import download_file
from app.utils.media import get_media_info

logger = logging.getLogger(__name__)

class FFmpegComposerService:
    """Service for composing and executing FFmpeg commands."""
    
    def __init__(self):
        """Initialize the FFmpeg composer service."""
        self.temp_dir = tempfile.gettempdir()
        logger.info("FFmpeg Composer Service initialized")
    
    def validate_request(self, request: FFmpegComposeRequest) -> List[str]:
        """
        Validate an FFmpeg compose request.
        
        Args:
            request: The FFmpeg compose request to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate inputs
        if not request.inputs:
            errors.append("At least one input file is required")
        
        for i, input_file in enumerate(request.inputs):
            if not input_file.file_url:
                errors.append(f"Input {i}: file_url is required")
        
        # Validate outputs
        if not request.outputs:
            errors.append("At least one output configuration is required")
        
        for i, output in enumerate(request.outputs):
            if not output.options:
                errors.append(f"Output {i}: at least one option is required")
        
        # Validate filters
        for i, filter_obj in enumerate(request.filters or []):
            if not filter_obj.filter:
                errors.append(f"Filter {i}: filter name is required")
        
        return errors
    
    def estimate_processing_time(self, request: FFmpegComposeRequest) -> float:
        """
        Estimate processing time for an FFmpeg operation.
        
        Args:
            request: The FFmpeg compose request
            
        Returns:
            Estimated processing time in seconds
        """
        # Basic estimation based on number of inputs, filters, and outputs
        base_time = 30.0  # Base 30 seconds
        
        # Add time for each input
        input_time = len(request.inputs) * 10.0
        
        # Add time for each filter
        filter_time = len(request.filters or []) * 15.0
        
        # Add time for each output
        output_time = len(request.outputs) * 20.0
        
        # Complex filters take longer
        complex_filter_time = 0.0
        for filter_obj in request.filters or []:
            if filter_obj.input_labels or filter_obj.output_label:
                complex_filter_time += 30.0
        
        total_time = base_time + input_time + filter_time + output_time + complex_filter_time
        
        # Cap at reasonable limits
        return min(max(total_time, 60.0), 1800.0)  # Between 1 minute and 30 minutes
    
    def compose_command(self, request: FFmpegComposeRequest) -> str:
        """
        Compose an FFmpeg command from the request.
        
        Args:
            request: The FFmpeg compose request
            
        Returns:
            The composed FFmpeg command string
        """
        cmd_parts = ["ffmpeg"]
        
        # Add global options
        for global_opt in request.global_options or []:
            cmd_parts.append(global_opt.option)
            if global_opt.argument is not None:
                cmd_parts.append(str(global_opt.argument))
        
        # Add inputs with their options
        for input_file in request.inputs:
            # Add input-specific options first
            for option in input_file.options or []:
                cmd_parts.append(option.option)
                if option.argument is not None:
                    cmd_parts.append(str(option.argument))
            
            # Add input file
            cmd_parts.extend(["-i", str(input_file.file_url)])
        
        # Add filters
        if request.filters:
            if request.use_simple_video_filter or request.use_simple_audio_filter:
                # Simple filters
                video_filters = []
                audio_filters = []
                
                for filter_obj in request.filters:
                    filter_str = filter_obj.filter
                    if filter_obj.arguments:
                        filter_str += "=" + ":".join(filter_obj.arguments)
                    
                    if filter_obj.type == "video":
                        video_filters.append(filter_str)
                    elif filter_obj.type == "audio":
                        audio_filters.append(filter_str)
                    else:
                        # Default to video if no type specified
                        video_filters.append(filter_str)
                
                if video_filters and request.use_simple_video_filter:
                    cmd_parts.extend(["-vf", ",".join(video_filters)])
                
                if audio_filters and request.use_simple_audio_filter:
                    cmd_parts.extend(["-af", ",".join(audio_filters)])
            else:
                # Complex filter graph
                filter_graph = self._build_filter_graph(request.filters)
                if filter_graph:
                    cmd_parts.extend(["-filter_complex", filter_graph])
        
        # Add global stream mappings
        for mapping in request.stream_mappings or []:
            cmd_parts.extend(["-map", mapping])
        
        # Add outputs
        for i, output in enumerate(request.outputs):
            # Add per-output stream mappings
            for mapping in output.stream_mappings or []:
                cmd_parts.extend(["-map", mapping])
            
            # Add output options
            for option in output.options:
                cmd_parts.append(option.option)
                if option.argument is not None:
                    cmd_parts.append(str(option.argument))
            
            # Add output filename (will be replaced with actual path during execution)
            output_filename = f"output_{i}.mp4"
            cmd_parts.append(output_filename)
        
        return " ".join(cmd_parts)
    
    def _build_filter_graph(self, filters: List[FFmpegFilter]) -> str:
        """
        Build a complex filter graph from filter objects.
        
        Args:
            filters: List of filter objects
            
        Returns:
            Filter graph string
        """
        filter_parts = []
        
        for filter_obj in filters:
            filter_str = ""
            
            # Add input labels
            if filter_obj.input_labels:
                input_refs = "".join(f"[{label}]" for label in filter_obj.input_labels)
                filter_str += input_refs
            
            # Add filter with arguments
            filter_str += filter_obj.filter
            if filter_obj.arguments:
                filter_str += "=" + ":".join(filter_obj.arguments)
            
            # Add output label
            if filter_obj.output_label:
                filter_str += f"[{filter_obj.output_label}]"
            
            filter_parts.append(filter_str)
        
        return ";".join(filter_parts)
    
    async def process_ffmpeg_compose(self, job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an FFmpeg compose job.
        
        Args:
            job_id: Unique job identifier
            params: Job parameters containing the FFmpeg compose request
            
        Returns:
            Result dictionary with output file information
        """
        start_time = time.time()
        request = FFmpegComposeRequest(**params)
        
        logger.info(f"Processing FFmpeg compose job {job_id} with {len(request.inputs)} inputs and {len(request.outputs)} outputs")
        
        # Validate request
        validation_errors = self.validate_request(request)
        if validation_errors:
            raise ValueError(f"Request validation failed: {'; '.join(validation_errors)}")
        
        # Create temporary working directory
        work_dir = os.path.join(self.temp_dir, f"ffmpeg_job_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            # Download input files
            input_paths = []
            for i, input_file in enumerate(request.inputs):
                logger.info(f"Downloading input {i}: {input_file.file_url}")
                
                # Determine file extension from URL
                parsed_url = urlparse(str(input_file.file_url))
                file_ext = os.path.splitext(parsed_url.path)[1] or ".mp4"
                input_path = os.path.join(work_dir, f"input_{i}{file_ext}")
                
                await download_file(str(input_file.file_url), input_path)
                input_paths.append(input_path)
            
            # Prepare output paths
            output_paths = []
            for i in range(len(request.outputs)):
                output_path = os.path.join(work_dir, f"output_{i}.mp4")
                output_paths.append(output_path)
            
            # Build and execute FFmpeg command
            cmd = self._build_ffmpeg_command(request, input_paths, output_paths)
            logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "FFmpeg execution failed"
                logger.error(f"FFmpeg command failed: {error_msg}")
                raise RuntimeError(f"FFmpeg execution failed: {error_msg}")
            
            logger.info("FFmpeg command executed successfully")
            
            # Upload output files and extract metadata
            output_results = []
            for i, output_path in enumerate(output_paths):
                if not os.path.exists(output_path):
                    raise RuntimeError(f"Output file {i} was not created")
                
                # Upload to S3 with unique suffix to prevent overwrites
                unique_suffix = uuid.uuid4().hex[:8]
                s3_key = f"ffmpeg_compose/{job_id}_{unique_suffix}/output_{i}.mp4"
                file_url = await s3_service.upload_file(output_path, s3_key)
                
                # Create output result
                clean_file_url = file_url.split("?")[0] if file_url else ""  # Remove query parameters
                output_result = FFmpegOutputResult.model_validate({
                    "file_url": clean_file_url
                })
                
                # Extract metadata if requested
                if request.metadata:
                    await self._extract_metadata(output_path, output_result, request.metadata, job_id, i)
                
                output_results.append(output_result)
            
            processing_time = time.time() - start_time
            
            # Create final result
            result = FFmpegComposeResult(
                outputs=output_results,
                command=" ".join(cmd),
                processing_time=processing_time
            )
            
            logger.info(f"FFmpeg compose job {job_id} completed in {processing_time:.2f} seconds")
            
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error in FFmpeg compose job {job_id}: {e}")
            raise
        finally:
            # Clean up temporary files
            try:
                import shutil
                shutil.rmtree(work_dir)
                logger.info(f"Cleaned up temporary directory: {work_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory {work_dir}: {e}")
    
    def _build_ffmpeg_command(
        self, 
        request: FFmpegComposeRequest, 
        input_paths: List[str], 
        output_paths: List[str]
    ) -> List[str]:
        """Build the actual FFmpeg command with file paths."""
        cmd = ["ffmpeg"]
        
        # Separate global options by their position requirements
        early_global_options = []
        late_global_options = []
        
        for global_opt in request.global_options or []:
            # Options that need to be placed after inputs (like -shortest)
            if global_opt.option in ["-shortest"]:
                late_global_options.append(global_opt)
            else:
                # Options that can be placed early (like -y, -ignore_unknown)
                early_global_options.append(global_opt)
        
        # Add early global options
        for global_opt in early_global_options:
            cmd.append(global_opt.option)
            if global_opt.argument is not None:
                cmd.append(str(global_opt.argument))
        
        # Always add overwrite flag if not specified
        if not any(opt.option == "-y" for opt in early_global_options):
            cmd.append("-y")
        
        # Add inputs with their options
        for i, (input_file, input_path) in enumerate(zip(request.inputs, input_paths)):
            # Add input-specific options first
            for option in input_file.options or []:
                cmd.append(option.option)
                if option.argument is not None:
                    cmd.append(str(option.argument))
            
            # Add input file
            cmd.extend(["-i", input_path])
        
        # Add filters
        if request.filters:
            if request.use_simple_video_filter or request.use_simple_audio_filter:
                # Simple filters
                video_filters = []
                audio_filters = []
                
                for filter_obj in request.filters:
                    filter_str = filter_obj.filter
                    if filter_obj.arguments:
                        filter_str += "=" + ":".join(filter_obj.arguments)
                    
                    if filter_obj.type == "video":
                        video_filters.append(filter_str)
                    elif filter_obj.type == "audio":
                        audio_filters.append(filter_str)
                    else:
                        # Default to video if no type specified
                        video_filters.append(filter_str)
                
                if video_filters and request.use_simple_video_filter:
                    cmd.extend(["-vf", ",".join(video_filters)])
                
                if audio_filters and request.use_simple_audio_filter:
                    cmd.extend(["-af", ",".join(audio_filters)])
            else:
                # Complex filter graph
                filter_graph = self._build_filter_graph(request.filters)
                if filter_graph:
                    cmd.extend(["-filter_complex", filter_graph])
        
        # Add global stream mappings
        for mapping in request.stream_mappings or []:
            cmd.extend(["-map", mapping])
        
        # Add late global options (like -shortest) that need to be placed after inputs
        for global_opt in late_global_options:
            cmd.append(global_opt.option)
            if global_opt.argument is not None:
                cmd.append(str(global_opt.argument))
        
        # Add outputs
        for i, (output, output_path) in enumerate(zip(request.outputs, output_paths)):
            # Add per-output stream mappings
            for mapping in output.stream_mappings or []:
                cmd.extend(["-map", mapping])
            
            # Add output options
            for option in output.options:
                cmd.append(option.option)
                if option.argument is not None:
                    cmd.append(str(option.argument))
            
            # Note: We do NOT auto-add -shortest flag
            # By default, FFmpeg will continue encoding until the longest stream ends,
            # which is the desired behavior for video compositions with audio
            # Users can explicitly add -shortest option in global_options array
            
            # Add output filename
            cmd.append(output_path)
        
        return cmd
    
    async def _extract_metadata(
        self, 
        output_path: str, 
        output_result: FFmpegOutputResult, 
        metadata_config: Any,
        job_id: str,
        output_index: int
    ) -> None:
        """Extract and add metadata to output result."""
        try:
            # Get file size if requested
            if metadata_config.filesize:
                output_result.filesize = os.path.getsize(output_path)
            
            # Get media info for duration, bitrate, encoder
            if metadata_config.duration or metadata_config.bitrate or metadata_config.encoder:
                try:
                    media_info = await get_media_info(output_path)
                    
                    if metadata_config.duration and media_info.get("duration"):
                        output_result.duration = float(media_info["duration"])
                    
                    if metadata_config.bitrate and media_info.get("bit_rate"):
                        output_result.bitrate = int(media_info["bit_rate"])
                    
                    if metadata_config.encoder and media_info.get("codec_name"):
                        output_result.encoder = media_info["codec_name"]
                        
                except Exception as e:
                    logger.warning(f"Failed to extract media info: {e}")
            
            # Generate thumbnail if requested
            if metadata_config.thumbnail:
                try:
                    thumbnail_path = os.path.join(
                        os.path.dirname(output_path), 
                        f"thumbnail_{output_index}.jpg"
                    )
                    
                    # Generate thumbnail using FFmpeg
                    thumbnail_cmd = [
                        "ffmpeg", "-y", "-i", output_path,
                        "-vf", "scale=320:240:force_original_aspect_ratio=decrease",
                        "-vframes", "1", "-q:v", "2",
                        thumbnail_path
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *thumbnail_cmd,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    await process.communicate()
                    
                    if process.returncode == 0 and os.path.exists(thumbnail_path):
                        # Upload thumbnail to S3
                        thumbnail_s3_key = f"ffmpeg_compose/{job_id}/thumbnail_{output_index}.jpg"
                        thumbnail_url = await s3_service.upload_file(thumbnail_path, thumbnail_s3_key)
                        clean_thumbnail_url = thumbnail_url.split("?")[0] if thumbnail_url else None
                        if clean_thumbnail_url:
                            # Use model reconstruction to properly handle AnyUrl conversion
                            output_data = output_result.model_dump()
                            output_data["thumbnail_url"] = clean_thumbnail_url
                            output_result = FFmpegOutputResult.model_validate(output_data)
                        
                        # Clean up local thumbnail
                        os.remove(thumbnail_path)
                        
                except Exception as e:
                    logger.warning(f"Failed to generate thumbnail: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

# Global service instance
ffmpeg_composer = FFmpegComposerService()