"""
Service for video concatenation operations.
"""
import os
import tempfile
import logging
import uuid
import subprocess
import asyncio
from typing import List, Dict, Any

from app.utils.media import download_media_file, SUPPORTED_VIDEO_FORMATS
from app.services.s3.s3 import s3_service
from app.models import VideoConcatenateResult

# Configure logging
logger = logging.getLogger(__name__)

async def concatenate_videos(job_id: str, video_urls: List[str], output_format: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Concatenate multiple videos into a single video.
    
    Args:
        job_id: The ID of the job.
        video_urls: List of video URLs to concatenate.
        output_format: Output video format (with leading dot).
        
    Returns:
        VideoConcatenateResult dictionary with the result of the concatenation.
        
    Raises:
        RuntimeError: If the process fails.
    """
    # Create temp directory for processing
    temp_dir = os.path.join("temp", f"concat_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Check if we need to use chunked processing
    use_chunked_processing = len(video_urls) > 5
    chunk_size = 5  # Process videos in chunks of 5
    
    try:
        if use_chunked_processing:
            # Use chunked processing for large number of videos
            final_output = await chunked_concatenation(job_id, video_urls, output_format, temp_dir, chunk_size, data)
        else:
            # Use standard processing for smaller number of videos
            final_output = await standard_concatenation(job_id, video_urls, output_format, temp_dir, data)
        
        # Check if S3 is initialized before attempting upload
        use_local_storage = False
        if not bool(s3_service.access_key and s3_service.secret_key and s3_service.bucket_name):
            logger.warning("S3 service not available, will use local storage as fallback")
            use_local_storage = True
            
        # If we're using local storage, save the file locally
        if use_local_storage:
            # Copy the file to a permanent local storage location
            local_storage_dir = os.path.join("storage", "videos")
            os.makedirs(local_storage_dir, exist_ok=True)
            local_output_path = os.path.join(local_storage_dir, f"concat_{job_id}{output_format}")
            
            import shutil
            shutil.copy2(final_output, local_output_path)
            
            # Clean up temporary files
            await cleanup_temp_files(temp_dir)
            
            # Return result with local file path
            return {
                "url": f"file://{os.path.abspath(local_output_path)}",
                "path": local_output_path
            }
        
        # Upload to S3 with retries
        for attempt in range(3):  # Try up to 3 times
            try:
                # Log file details before upload
                file_size = os.path.getsize(final_output)
                logger.info(f"Attempting to upload file (size: {file_size} bytes) to S3 (attempt {attempt+1}/3)")
                
                # Upload to S3
                object_name = f"videos/concat_{job_id}{output_format}"
                upload_result = await s3_service.upload_file(final_output, object_name)
                
                if not upload_result:
                    logger.error(f"Failed to upload concatenated video (attempt {attempt+1}/3)")
                    if attempt < 2:  # Don't sleep on last attempt
                        await asyncio.sleep(2 * (attempt + 1))  # Progressive backoff
                    continue
                    
                # Clean up temporary files
                await cleanup_temp_files(temp_dir)

                #remove signed url from s3
                upload_result = upload_result.split("?")[0]
                
                # Return result as VideoConcatenateResult dict
                return {
                    "url": upload_result,  # upload_result is already the URL string
                    "path": object_name
                }
            except Exception as e:
                logger.error(f"Error uploading to S3 (attempt {attempt+1}/3): {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(2 * (attempt + 1))  # Progressive backoff
        
        # If we got here, all upload attempts failed, use local storage as fallback
        logger.warning("All S3 upload attempts failed, using local storage as fallback")
        
        # Copy the file to a permanent local storage location
        local_storage_dir = os.path.join("storage", "videos")
        os.makedirs(local_storage_dir, exist_ok=True)
        local_output_path = os.path.join(local_storage_dir, f"concat_{job_id}{output_format}")
        
        import shutil
        shutil.copy2(final_output, local_output_path)
        
        # Clean up temporary files
        await cleanup_temp_files(temp_dir)
        
        # Return result with local file path
        return {
            "url": f"file://{os.path.abspath(local_output_path)}",
            "path": local_output_path
        }
    
    except Exception as e:
        logger.error(f"Error in video concatenation job {job_id}: {e}")
        # Clean up any temporary files if we got this far
        try:
            if os.path.exists(temp_dir):
                await cleanup_temp_files(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
        
        raise

async def standard_concatenation(job_id: str, video_urls: List[str], output_format: str, temp_dir: str, data: Dict[str, Any] | None = None) -> str:
    """
    Standard concatenation process for a smaller number of videos.
    
    Args:
        job_id: The ID of the job.
        video_urls: List of video URLs to concatenate.
        output_format: Output video format.
        temp_dir: Temporary directory for processing.
        
    Returns:
        Path to the output file.
    """
    # File to hold input file list for ffmpeg
    input_list_file = os.path.join(temp_dir, "input_list.txt")
    downloaded_files = []
    
    # Download all videos
    logger.info(f"Starting to download {len(video_urls)} videos for job {job_id}")
    for i, url in enumerate(video_urls):
        try:
            # Convert Pydantic URL objects to strings
            url_str = str(url) if url else None
            if not url_str:
                raise RuntimeError(f"Invalid URL at index {i}: URL is empty or None")
            
            # Download the video
            local_path, file_ext = await download_media_file(url_str, temp_dir)
            if not os.path.exists(local_path):
                raise RuntimeError(f"Failed to download video from {url_str}")
            
            downloaded_files.append(local_path)
            logger.info(f"Downloaded video {i+1}/{len(video_urls)} to {local_path}")
        except Exception as e:
            logger.error(f"Error downloading video {i+1} from {url}: {e}")
            raise RuntimeError(f"Failed to download video {i+1}: {str(e)}")
    
    # Generate output filename
    output_file = os.path.join(temp_dir, f"concatenated{output_format}")
    
    # Create file list for ffmpeg
    with open(input_list_file, "w") as f:
        for video_file in downloaded_files:
            f.write(f"file '{os.path.abspath(video_file)}'\n")
    
    # Check if we need duration limiting
    if data is None:
        data = {}
    
    max_segment_duration = data.get("max_segment_duration")
    total_duration_limit = data.get("total_duration_limit")
    
    # Run ffmpeg to concatenate videos
    if max_segment_duration or total_duration_limit:
        # Use re-encoding with duration limits
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", input_list_file,
            "-c:v", "libx264",
            "-c:a", "aac"
        ]
        
        # Add total duration limit if specified
        if total_duration_limit:
            ffmpeg_cmd.extend(["-t", str(total_duration_limit)])
            
        ffmpeg_cmd.extend(["-y", output_file])
        logger.info(f"Using re-encoding with duration limit: {total_duration_limit}s")
    else:
        # Use fast stream copy (no duration limits) 
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", input_list_file,
            "-c", "copy",  # Use stream copy, much faster than re-encoding
            "-y",
            output_file
        ]
        logger.info("Using fast stream copy (no duration limits)")
    
    logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minute timeout
        
        if process.returncode != 0:
            logger.error(f"ffmpeg failed: {stderr.decode()}")
            raise RuntimeError(f"Failed to concatenate videos: {stderr.decode()}")
    except asyncio.TimeoutError:
        logger.error("FFmpeg process timed out after 5 minutes")
        if process:
            process.terminate()
            await process.wait()
        raise RuntimeError("Video concatenation timed out")
    
    # Check if output file exists and has valid size
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        logger.error("Output file is missing or empty")
        raise RuntimeError("Failed to create output file")
        
    return output_file

async def chunked_concatenation(job_id: str, video_urls: List[str], output_format: str, temp_dir: str, chunk_size: int, data: Dict[str, Any] | None = None) -> str:
    """
    Process videos in chunks for better memory usage with large numbers of videos.
    
    Args:
        job_id: The ID of the job.
        video_urls: List of video URLs to concatenate.
        output_format: Output video format.
        temp_dir: Temporary directory for processing.
        chunk_size: Number of videos to process in each chunk.
        
    Returns:
        Path to the final output file.
    """
    # Create chunks directory
    chunks_dir = os.path.join(temp_dir, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    
    # Split videos into chunks
    chunks = [video_urls[i:i + chunk_size] for i in range(0, len(video_urls), chunk_size)]
    logger.info(f"Processing {len(video_urls)} videos in {len(chunks)} chunks of {chunk_size}")
    
    # Process each chunk and get intermediate output files
    intermediate_files = []
    for i, chunk in enumerate(chunks):
        chunk_output = os.path.join(chunks_dir, f"chunk_{i}{output_format}")
        
        # File to hold input file list for ffmpeg
        chunk_list_file = os.path.join(chunks_dir, f"chunk_list_{i}.txt")
        downloaded_chunk_files = []
        
        # Download videos in this chunk
        logger.info(f"Starting to download chunk {i+1}/{len(chunks)} ({len(chunk)} videos)")
        for j, url in enumerate(chunk):
            try:
                # Convert Pydantic URL objects to strings
                url_str = str(url) if url else None
                if not url_str:
                    raise RuntimeError(f"Invalid URL at index {j}: URL is empty or None")
                
                # Download the video
                local_path, file_ext = await download_media_file(url_str, chunks_dir)
                if not os.path.exists(local_path):
                    raise RuntimeError(f"Failed to download video from {url_str}")
                
                downloaded_chunk_files.append(local_path)
                logger.info(f"Downloaded video {j+1}/{len(chunk)} in chunk {i+1}")
            except Exception as e:
                logger.error(f"Error downloading video in chunk {i+1}: {e}")
                raise RuntimeError(f"Failed to download video in chunk {i+1}: {str(e)}")
        
        # Create file list for ffmpeg
        with open(chunk_list_file, "w") as f:
            for video_file in downloaded_chunk_files:
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        # Run ffmpeg to concatenate this chunk
        chunk_ffmpeg_cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", chunk_list_file,
            "-c", "copy",
            chunk_output
        ]
        
        logger.info(f"Running ffmpeg for chunk {i+1}/{len(chunks)}")
        chunk_process = None
        try:
            chunk_process = await asyncio.create_subprocess_exec(
                *chunk_ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            chunk_stdout, chunk_stderr = await asyncio.wait_for(chunk_process.communicate(), timeout=300)
            
            if chunk_process.returncode != 0:
                logger.error(f"ffmpeg failed for chunk {i+1}: {chunk_stderr.decode()}")
                raise RuntimeError(f"Failed to concatenate chunk {i+1}: {chunk_stderr.decode()}")
        except asyncio.TimeoutError:
            logger.error(f"FFmpeg process timed out for chunk {i+1}")
            if chunk_process:
                chunk_process.terminate()
                await chunk_process.wait()
            raise RuntimeError(f"Video concatenation timed out for chunk {i+1}")
        
        # Check if chunk output exists
        if not os.path.exists(chunk_output) or os.path.getsize(chunk_output) == 0:
            logger.error(f"Chunk {i+1} output file is missing or empty")
            raise RuntimeError(f"Failed to create chunk {i+1} output file")
            
        intermediate_files.append(chunk_output)
        
        # Clean up downloaded files for this chunk to save space
        for file in downloaded_chunk_files:
            try:
                os.remove(file)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file}: {e}")
    
    # Now concatenate all chunks
    final_output = os.path.join(temp_dir, f"concatenated{output_format}")
    final_list_file = os.path.join(temp_dir, "final_list.txt")
    
    # Create file list for final concatenation
    with open(final_list_file, "w") as f:
        for chunk_file in intermediate_files:
            f.write(f"file '{os.path.abspath(chunk_file)}'\n")
    
    # Run ffmpeg to concatenate all chunks
    final_ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", final_list_file,
        "-c", "copy",
        final_output
    ]
    
    logger.info("Running final concatenation of all chunks")
    final_process = None
    try:
        final_process = await asyncio.create_subprocess_exec(
            *final_ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        final_stdout, final_stderr = await asyncio.wait_for(final_process.communicate(), timeout=300)
        
        if final_process.returncode != 0:
            logger.error(f"Final ffmpeg failed: {final_stderr.decode()}")
            raise RuntimeError(f"Failed to concatenate all chunks: {final_stderr.decode()}")
    except asyncio.TimeoutError:
        logger.error("Final FFmpeg process timed out")
        if final_process:
            final_process.terminate()
            await final_process.wait()
        raise RuntimeError("Final video concatenation timed out")
    
    # Check if final output exists
    if not os.path.exists(final_output) or os.path.getsize(final_output) == 0:
        logger.error("Final output file is missing or empty")
        raise RuntimeError("Failed to create final output file")
    
    return final_output

async def cleanup_temp_files(temp_dir: str):
    """
    Clean up temporary files created during processing.
    
    Args:
        temp_dir: Directory containing temporary files
    """
    try:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")

# Helper functions for diagnostics
async def check_s3_configuration() -> Dict[str, Any]:
    """
    Check S3 configuration and return diagnostic information.
    
    Returns:
        Dictionary with:
            initialized: Whether S3 is initialized
            details: Diagnostic details
            env_vars: Environment variables (masked)
            bucket: Bucket name being used
    """
    import os
    
    # Check if storage manager has the necessary attributes for functionality
    # instead of relying on a specific 'is_initialized' attribute
    is_initialized = bool(s3_service.access_key and s3_service.secret_key and s3_service.bucket_name)
    bucket_name = getattr(s3_service, 'bucket_name', 'Not set')
    
    # Get environment variables (masked for security)
    env_vars = {
        "S3_REGION": os.environ.get("S3_REGION", "Not set"),
        "S3_BUCKET_NAME": os.environ.get("S3_BUCKET_NAME", "Not set"),
        "S3_ACCESS_KEY": "***" if os.environ.get("S3_ACCESS_KEY") else "Not set",
        "S3_SECRET_KEY": "***" if os.environ.get("S3_SECRET_KEY") else "Not set"
    }
    
    # Details based on initialization status
    if is_initialized:
        details = f"S3 storage is properly initialized with bucket '{bucket_name}'"
    else:
        details = "S3 storage is not initialized. Check AWS credentials and bucket configuration."
        
        # Add more specific diagnostics
        if not env_vars["S3_REGION"]:
            details += " S3_REGION is not set."
        
        if not env_vars["S3_BUCKET_NAME"]:
            details += " No bucket name is set (check S3_BUCKET_NAME)."
        else:
            details += f" Using S3_BUCKET_NAME='{bucket_name}'."
        
        if not os.environ.get("S3_ACCESS_KEY"):
            details += " S3_ACCESS_KEY is not set."
        
        if not os.environ.get("S3_SECRET_KEY"):
            details += " S3_SECRET_KEY is not set."
    
    return {
        "initialized": is_initialized,
        "details": details,
        "env_vars": env_vars,
        "bucket": bucket_name
    }

class VideoConcatenationService:
    """Service for video concatenation operations."""
    
    @staticmethod
    async def process_job(job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a video concatenation job.
        
        Args:
            job_id: The ID of the job.
            data: The job data containing video URLs and output format.
            
        Returns:
            Dictionary with the result of the concatenation, following VideoConcatenateResult structure.
            
        Raises:
            Exception: If the process fails.
        """
        try:
            video_urls = data.get("video_urls", [])
            output_format = data.get("output_format", ".mp4")
            
            # Add progress logging
            logger.info(f"Starting video concatenation job {job_id} with {len(video_urls)} videos")
            
            # Check S3 configuration before starting
            s3_status = await check_s3_configuration()
            if not s3_status["initialized"]:
                logger.warning(f"S3 storage not properly initialized: {s3_status['details']}")
                
                # Log all environment variables for debugging
                for var, value in s3_status["env_vars"].items():
                    logger.debug(f"S3 config - {var}: {value}")
                    
                # Log that we'll continue with local storage fallback
                logger.warning("S3 not available. Videos will be stored locally as fallback.")
            else:
                logger.info(f"S3 properly configured with bucket: {s3_status['bucket']}")
                
            result = await concatenate_videos(job_id, video_urls, output_format, data)
            
            # Check if the result has a proper S3 URL or a local file path
            if "url" in result and result["url"].startswith("file://"):
                logger.warning(f"Job {job_id} completed but video stored locally, not in S3: {result['path']}")
            else:
                logger.info(f"Successfully completed video concatenation job {job_id} with S3 upload: {result['url']}")
            
            return result
        except Exception as e:
            logger.error(f"Error in concatenation job {job_id}: {e}")
            raise

# Create a singleton instance
concatenation_service = VideoConcatenationService() 