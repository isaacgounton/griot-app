import os
import tempfile
import uuid
import json
import logging
import asyncio
from typing import Any

from app.services.s3.s3_service import S3UploadService
from app.utils.simone.downloader import Downloader
from app.utils.simone.transcriber import Transcriber
from app.utils.simone.blogger import Blogger
from app.utils.simone.summarizer import Summarizer
from app.utils.simone.framer import Framer
from app.utils.simone.scorer import Scorer
from app.utils.simone.saver import Saver
from app.utils.simone.social_media_generator import SocialMediaGenerator

logger = logging.getLogger(__name__)


class SimoneService:
    """Service for processing videos into blog posts with AI-powered content generation."""

    def __init__(self):
        self.s3_service = S3UploadService()

    async def process_video_to_blog(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Process a video into a blog post with screenshots.

        Args:
            params: Dictionary containing:
                - url: Video URL to process
                - platform: Optional social media platform
                - cookies_content: Optional cookie content
                - cookies_url: Optional cookie URL

        Returns:
            Dictionary with blog content, screenshots, and file URLs
        """
        url = params["url"]
        platform = params.get("platform")
        cookies_content = params.get("cookies_content")
        cookies_url = params.get("cookies_url")

        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")

        tesseract_path = os.environ.get("TESSERACT_PATH", "/usr/bin/tesseract")
        output_dir_name = str(uuid.uuid4())

        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Processing in temporary directory: {tmpdir}")

            # Use absolute paths throughout - no os.chdir() to avoid race conditions
            video_path = os.path.join(tmpdir, "video.mp4")
            audio_path = os.path.join(tmpdir, "audio.mp4")
            transcription_path = os.path.join(tmpdir, "transcription.txt")
            blogpost_path = os.path.join(tmpdir, "generated_blogpost.txt")

            # Download video and audio
            logger.info("Downloading audio and video...")
            downloader = Downloader(url=url, cookies_content=cookies_content, cookies_url=cookies_url, work_dir=tmpdir)

            await asyncio.to_thread(downloader.video)
            if not os.path.exists(video_path):
                raise Exception("Failed to download video.mp4")

            await asyncio.to_thread(downloader.audio)
            if not os.path.exists(audio_path):
                raise Exception("Failed to download audio.mp4")

            logger.info("Audio and video downloaded successfully")

            # Transcribe audio
            logger.info("Transcribing audio...")
            transcriber = Transcriber(audio_path, work_dir=tmpdir)
            await transcriber.transcribe()

            # Generate keywords
            logger.info("Generating keywords...")
            summarizer = Summarizer(api_key=openai_api_key, transcription_filename=transcription_path)
            keyword_text = await asyncio.to_thread(summarizer.generate_summary)
            keyword_list = [k.strip() for k in keyword_text.replace(",", "\n").split("\n") if k.strip()]

            # Generate blog post
            logger.info("Generating blog post...")
            blogger = Blogger(openai_api_key, transcription_path, blogpost_path)
            await asyncio.to_thread(blogger.generate_blogpost)

            # Generate social media post if platform specified
            social_media_post_content = ""
            if platform:
                logger.info(f"Generating social media post for {platform}...")
                social_media_generator = SocialMediaGenerator(openai_api_key, transcription_path)
                social_media_post_content = await asyncio.to_thread(social_media_generator.generate_post, platform)

            # Process video frames
            logger.info("Processing video frames...")
            framer = Framer(video_path)
            frame_list = await asyncio.to_thread(framer.get_video_frames)

            scorer = Scorer(frame_list, keyword_list, tesseract_path)
            score_list = await asyncio.to_thread(scorer.score_frames)

            # Save screenshots
            logger.info("Saving screenshots...")
            saver_output = os.path.join(tmpdir, "simone_saver_outputs")
            os.makedirs(saver_output, exist_ok=True)
            saver = Saver(frame_list, score_list, saver_output)
            saver.save_best_frames()

            # Read generated content
            blog_post_content = self._read_file(blogpost_path)
            transcription_content = self._read_file(transcription_path)

            # Store files to S3
            result = await self._store_files(
                output_dir_name=output_dir_name,
                temp_output_for_saver=saver_output,
                blog_post_path=blogpost_path,
                blog_post_content=blog_post_content,
                transcription_path=transcription_path,
                transcription_content=transcription_content,
                social_media_post_content=social_media_post_content
            )

            logger.info("Video processing completed successfully")
            return result

    async def process_video_with_enhanced_features(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Process video with enhanced features including viral content generation.
        """
        url = params["url"]
        include_topics = params.get("include_topics", True)
        include_x_thread = params.get("include_x_thread", True)
        platforms = params.get("platforms", ["x", "linkedin", "instagram"])
        thread_config = params.get("thread_config", {
            "max_posts": 8,
            "character_limit": 280,
            "thread_style": "viral"
        })
        cookies_content = params.get("cookies_content")
        cookies_url = params.get("cookies_url")

        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not found")

        tesseract_path = os.environ.get("TESSERACT_PATH", "/usr/bin/tesseract")
        output_dir_name = str(uuid.uuid4())

        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Enhanced processing in temporary directory: {tmpdir}")

            video_path = os.path.join(tmpdir, "video.mp4")
            audio_path = os.path.join(tmpdir, "audio.mp4")
            transcription_path = os.path.join(tmpdir, "transcription.txt")
            blogpost_path = os.path.join(tmpdir, "generated_blogpost.txt")

            # Download video and audio
            logger.info("Downloading audio and video...")
            downloader = Downloader(url=url, cookies_content=cookies_content, cookies_url=cookies_url, work_dir=tmpdir)

            await asyncio.to_thread(downloader.video)
            if not os.path.exists(video_path):
                raise Exception("Failed to download video.mp4")

            await asyncio.to_thread(downloader.audio)
            if not os.path.exists(audio_path):
                raise Exception("Failed to download audio.mp4")

            # Transcribe with enhanced features
            logger.info("Transcribing audio with enhanced features...")
            transcriber = Transcriber(audio_path, work_dir=tmpdir)
            await transcriber.transcribe()

            # Check for SRT file
            srt_path = os.path.join(tmpdir, "audio.srt")
            srt_filename = srt_path if os.path.exists(srt_path) else None

            # Generate enhanced content package
            logger.info("Generating enhanced content with topics and threads...")
            social_media_generator = SocialMediaGenerator(
                openai_api_key,
                transcription_path,
                srt_filename
            )

            content_package = await asyncio.to_thread(
                social_media_generator.generate_viral_content_package,
                platforms=platforms,
                include_topics=include_topics,
                include_thread=include_x_thread,
                **thread_config
            )

            # Generate traditional blog post
            logger.info("Generating blog post...")
            blogger = Blogger(openai_api_key, transcription_path, blogpost_path)
            await asyncio.to_thread(blogger.generate_blogpost)

            # Generate keywords for frame scoring
            logger.info("Generating keywords for frame analysis...")
            summarizer = Summarizer(api_key=openai_api_key, transcription_filename=transcription_path)
            keyword_text = await asyncio.to_thread(summarizer.generate_summary)
            keyword_list = [k.strip() for k in keyword_text.replace(",", "\n").split("\n") if k.strip()]

            # Process video frames
            logger.info("Processing video frames...")
            framer = Framer(video_path)
            frame_list = await asyncio.to_thread(framer.get_video_frames)

            scorer = Scorer(frame_list, keyword_list, tesseract_path)
            score_list = await asyncio.to_thread(scorer.score_frames)

            # Save screenshots
            logger.info("Saving screenshots...")
            saver_output = os.path.join(tmpdir, "simone_saver_outputs")
            os.makedirs(saver_output, exist_ok=True)
            saver = Saver(frame_list, score_list, saver_output)
            saver.save_best_frames()

            # Read generated content
            blog_post_content = self._read_file(blogpost_path)
            transcription_content = self._read_file(transcription_path)

            # Save content package to file
            content_package_path = os.path.join(tmpdir, "viral_content_package.json")
            with open(content_package_path, "w", encoding="utf-8") as f:
                json.dump(content_package, f, indent=2, ensure_ascii=False)

            # Handle enhanced file storage
            result = await self._store_enhanced_files(
                output_dir_name=output_dir_name,
                temp_output_for_saver=saver_output,
                blog_post_path=blogpost_path,
                blog_post_content=blog_post_content,
                transcription_path=transcription_path,
                transcription_content=transcription_content,
                content_package=content_package,
                content_package_path=content_package_path,
                include_topics=include_topics,
                include_x_thread=include_x_thread,
                platforms=platforms,
                thread_config=thread_config
            )

            logger.info("Enhanced video processing completed successfully")
            return result


    def _read_file(self, filepath: str) -> str:
        """Safely read file content."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    async def _store_files(self, output_dir_name: str, temp_output_for_saver: str,
                          blog_post_path: str, blog_post_content: str,
                          transcription_path: str, transcription_content: str,
                          social_media_post_content: str) -> dict[str, Any]:
        """Store generated files to S3."""
        output_blog_post_url = ""
        output_screenshot_urls: list[str] = []
        output_transcription_url = ""

        logger.info("Uploading outputs to S3...")

        if blog_post_content:
            output_blog_post_url = await self.s3_service.upload_file(
                blog_post_path,
                f"simone_outputs/{output_dir_name}/generated_blogpost.txt",
                content_type="text/plain"
            )

        if transcription_content and os.path.exists(transcription_path):
            output_transcription_url = await self.s3_service.upload_file(
                transcription_path,
                f"simone_outputs/{output_dir_name}/transcription.txt",
                content_type="text/plain"
            )

        for f_name in os.listdir(temp_output_for_saver):
            if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                file_path_to_upload = os.path.join(temp_output_for_saver, f_name)
                screenshot_url = await self.s3_service.upload_file(
                    file_path_to_upload,
                    f"simone_outputs/{output_dir_name}/{f_name}",
                    content_type="image/png"
                )
                output_screenshot_urls.append(screenshot_url)

        logger.info("Outputs uploaded to S3 successfully")

        return {
            "blog_post_content": blog_post_content,
            "blog_post_url": output_blog_post_url,
            "screenshots": output_screenshot_urls,
            "social_media_post_content": social_media_post_content,
            "transcription_content": transcription_content,
            "transcription_url": output_transcription_url
        }

    async def _store_enhanced_files(self, output_dir_name: str, temp_output_for_saver: str,
                                   blog_post_path: str, blog_post_content: str,
                                   transcription_path: str, transcription_content: str,
                                   content_package: dict, content_package_path: str,
                                   include_topics: bool, include_x_thread: bool,
                                   platforms: list[str], thread_config: dict) -> dict[str, Any]:
        """Store enhanced generated files to S3."""
        output_blog_post_url = ""
        output_screenshot_urls: list[str] = []
        content_package_url = ""
        output_transcription_url = ""

        logger.info("Uploading enhanced outputs to S3...")

        if blog_post_content:
            output_blog_post_url = await self.s3_service.upload_file(
                blog_post_path,
                f"simone_outputs/{output_dir_name}/generated_blogpost.txt",
                content_type="text/plain"
            )

        content_package_url = await self.s3_service.upload_file(
            content_package_path,
            f"simone_outputs/{output_dir_name}/viral_content_package.json",
            content_type="application/json"
        )

        if transcription_content and os.path.exists(transcription_path):
            output_transcription_url = await self.s3_service.upload_file(
                transcription_path,
                f"simone_outputs/{output_dir_name}/transcription.txt",
                content_type="text/plain"
            )

        for f_name in os.listdir(temp_output_for_saver):
            if f_name.startswith("screenshot_") and f_name.endswith(".png"):
                file_path_to_upload = os.path.join(temp_output_for_saver, f_name)
                screenshot_url = await self.s3_service.upload_file(
                    file_path_to_upload,
                    f"simone_outputs/{output_dir_name}/{f_name}",
                    content_type="image/png"
                )
                output_screenshot_urls.append(screenshot_url)

        logger.info("Enhanced outputs uploaded to S3 successfully")

        return {
            "blog_post_content": blog_post_content,
            "blog_post_url": output_blog_post_url,
            "screenshots": output_screenshot_urls,
            "viral_content_package": content_package,
            "content_package_url": content_package_url,
            "transcription_content": transcription_content,
            "transcription_url": output_transcription_url,
            "enhanced_features": {
                "topics_included": include_topics,
                "x_thread_included": include_x_thread,
                "platforms_processed": platforms,
                "thread_config": thread_config
            },
            "processing_summary": {
                "total_topics": len(content_package.get('content', {}).get('topics', {}).get('topics', [])) if include_topics else 0,
                "thread_posts": len(content_package.get('content', {}).get('x_thread', {}).get('thread', [])) if include_x_thread else 0,
                "platforms_generated": list(content_package.get('content', {}).get('posts', {}).keys()),
                "screenshots_count": len(output_screenshot_urls)
            }
        }
