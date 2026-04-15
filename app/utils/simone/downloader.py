from __future__ import annotations

import yt_dlp
import os
import time
import random
import logging
import requests

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, url, cookies_content=None, cookies_url=None, work_dir=None):
        self.url = url
        self.cookies_content = cookies_content
        self.cookies_url = cookies_url
        self.work_dir = work_dir or os.getcwd()
        self._auto_cookies_path: str | None = None

    def _try_auto_extract_cookies(self) -> str | None:
        """Attempt to extract fresh YouTube cookies via Playwright profile."""
        try:
            from app.utils.youtube_cookies import get_cookies_sync
            cookies_path = get_cookies_sync()
            if os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 100:
                logger.info(f"Auto-extracted fresh YouTube cookies to {cookies_path}")
                self._auto_cookies_path = cookies_path
                return cookies_path
        except Exception as e:
            logger.debug(f"Auto cookie extraction not available: {e}")
        return None

    def _download_cookies_from_url(self, cookies_url, temp_dir):
        """Download cookies from URL and save to local file"""
        try:
            response = requests.get(cookies_url, timeout=30)
            response.raise_for_status()
            
            cookies_path = os.path.join(temp_dir, 'downloaded_cookies.txt')
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Downloaded cookies from URL to {cookies_path}")
            return cookies_path
        except Exception as e:
            logger.error(f"Failed to download cookies from URL {cookies_url}: {e}")
            return None
    
    def _get_ydl_opts(self, format_selector, output_filename, auth_method='auto'):
        """Get yt-dlp options with enhanced authentication and anti-detection measures"""
        temp_dir = self.work_dir
        
        # Base yt-dlp options with anti-detection measures
        ydl_opts = {
            'format': format_selector,
            'outtmpl': output_filename,
            'no_warnings': False,
            'ignoreerrors': False,
            'quiet': False,
            'verbose': False,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K',
            # Anti-detection headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Additional anti-detection measures
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'sleep_interval_requests': 1,
        }

        # Handle authentication methods
        if auth_method == 'cookies_content' and self.cookies_content:
            cookies_path = os.path.join(temp_dir, 'cookies.txt')
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write(self.cookies_content)
            ydl_opts['cookiefile'] = cookies_path
            logger.info(f"Using cookies from content, saved to {cookies_path}")
        elif auth_method == 'cookies_url' and self.cookies_url:
            # Download cookies from URL
            cookies_path = self._download_cookies_from_url(self.cookies_url, temp_dir)
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts['cookiefile'] = cookies_path
                logger.info(f"Using cookies downloaded from URL: {cookies_path}")
            else:
                logger.warning(f"Failed to download cookies from URL: {self.cookies_url}")
        elif auth_method == 'cookies_file':
            # Look for existing cookies file
            cookies_path = os.path.join(temp_dir, 'cookies.txt')
            if os.path.exists(cookies_path):
                ydl_opts['cookiefile'] = cookies_path
                logger.info(f"Using existing cookies file: {cookies_path}")
        elif auth_method == 'auto_extract':
            # Auto-extract from Playwright profile
            cookies_path = self._try_auto_extract_cookies()
            if cookies_path:
                ydl_opts['cookiefile'] = cookies_path
                logger.info(f"Using auto-extracted cookies: {cookies_path}")

        return ydl_opts

    def _test_video_access(self, ydl_opts):
        """Test if we can access the video before attempting download"""
        try:
            test_opts = ydl_opts.copy()
            test_opts.update({
                'simulate': True,
                'quiet': True,
                'no_warnings': True,
            })
            
            with yt_dlp.YoutubeDL(test_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
            if info and info.get('title'):
                logger.info(f"Video access test successful: {info.get('title', 'Unknown title')}")
                return True
            else:
                logger.warning("Video access test failed: No video info returned")
                return False
                
        except Exception as e:
            logger.warning(f"Video access test failed: {e}")
            return False

    def audio(self):
        """Download audio using yt-dlp with multiple authentication and format strategies"""
        # Prioritize methods based on what's available
        auth_methods = []
        if self.cookies_content:
            auth_methods.append('cookies_content')
        if self.cookies_url:
            auth_methods.append('cookies_url')
        auth_methods.extend(['cookies_file', 'auto_extract', 'auto'])

        format_strategies = [
            ('bestaudio[ext=m4a]', os.path.join(self.work_dir, 'audio.m4a')),
            ('bestaudio[ext=mp4]', os.path.join(self.work_dir, 'audio.mp4')),
            ('bestaudio/best', os.path.join(self.work_dir, 'audio.%(ext)s')),
        ]

        for auth_method in auth_methods:
            logger.info(f"Trying audio download with auth method: {auth_method}")

            for format_selector, output_template in format_strategies:
                try:
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))

                    ydl_opts = self._get_ydl_opts(format_selector, output_template, auth_method)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                    # Check if file was downloaded and rename to expected filename
                    target_path = os.path.join(self.work_dir, 'audio.mp4')
                    downloaded_files = [f for f in os.listdir(self.work_dir) if f.startswith('audio.')]
                    if downloaded_files:
                        downloaded_file = os.path.join(self.work_dir, downloaded_files[0])
                        if downloaded_file != target_path:
                            os.rename(downloaded_file, target_path)
                        logger.info(f"Audio downloaded successfully as audio.mp4 using {auth_method}")
                        return

                except Exception as e:
                    logger.debug(f"Audio download failed with {auth_method} and format {format_selector}: {e}")
                    continue

            # If we get here, all formats failed for this auth method
            logger.warning(f"All audio formats failed for auth method: {auth_method}")

        raise Exception("All audio download strategies and authentication methods failed")

    def video(self):
        """Download video using yt-dlp with multiple authentication and format strategies"""
        # Prioritize methods based on what's available
        auth_methods = []
        if self.cookies_content:
            auth_methods.append('cookies_content')
        if self.cookies_url:
            auth_methods.append('cookies_url')
        auth_methods.extend(['cookies_file', 'auto'])

        format_strategies = [
            ('best[height<=720][ext=mp4]', os.path.join(self.work_dir, 'video.mp4')),
            ('best[ext=mp4]', os.path.join(self.work_dir, 'video.mp4')),
            ('best', os.path.join(self.work_dir, 'video.%(ext)s')),
        ]

        for auth_method in auth_methods:
            logger.info(f"Trying video download with auth method: {auth_method}")

            # Test access first with this auth method
            test_ydl_opts = self._get_ydl_opts('best', os.path.join(self.work_dir, 'test.%(ext)s'), auth_method)
            if not self._test_video_access(test_ydl_opts):
                logger.warning(f"Video access test failed for auth method: {auth_method}, skipping...")
                continue

            for format_selector, output_template in format_strategies:
                try:
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(1.0, 2.0))

                    ydl_opts = self._get_ydl_opts(format_selector, output_template, auth_method)

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([self.url])

                    # Check if file was downloaded and rename to expected filename
                    target_path = os.path.join(self.work_dir, 'video.mp4')
                    downloaded_files = [f for f in os.listdir(self.work_dir) if f.startswith('video.')]
                    if downloaded_files:
                        downloaded_file = os.path.join(self.work_dir, downloaded_files[0])
                        if downloaded_file != target_path:
                            os.rename(downloaded_file, target_path)
                        logger.info(f"Video downloaded successfully as video.mp4 using {auth_method}")
                        return

                except Exception as e:
                    logger.debug(f"Video download failed with {auth_method} and format {format_selector}: {e}")
                    continue

            # If we get here, all formats failed for this auth method
            logger.warning(f"All video formats failed for auth method: {auth_method}")

        raise Exception("All video download strategies and authentication methods failed")