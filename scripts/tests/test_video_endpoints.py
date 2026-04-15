#!/usr/bin/env python3
"""
Test script for all video endpoints in the Griot.

This script tests all video-related endpoints to ensure they are working correctly.
It covers video generation, manipulation, text overlay, thumbnails, and management.

Usage:
    python test_video_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

Environment Variables:
    API_KEY: The main API key for authentication
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VideoEndpointTester:
    """Test class for video endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('API_KEY')
        self.session = requests.Session()
        self.test_results = []

        if not self.api_key:
            raise ValueError("API_KEY environment variable or --api-key parameter is required")

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        })

    def log_test_result(self, endpoint: str, method: str, success: bool, response_data: Any = None, error: str = None):
        """Log a test result."""
        result = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'success': success,
            'response_data': response_data,
            'error': error
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {method} {endpoint}")
        if error:
            print(f"   Error: {error}")

    def test_video_generation(self):
        """Test video generation endpoints."""
        print("\n🎬 Testing Video Generation Endpoints...")

        # Test POST /generate - AI video generation
        try:
            payload = {
                "prompt": "A beautiful sunset over mountains with flowing water",
                "provider": "ltx_video",
                "negative_prompt": "blurry, low quality",
                "width": 704,
                "height": 480,
                "num_frames": 49,
                "num_inference_steps": 20
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/generate", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/generate", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/generate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/generate", "POST", False, error=str(e))

    def test_video_from_image(self):
        """Test video generation from image."""
        print("\n🖼️ Testing Video from Image...")

        # Test POST /from-image - Generate video from image
        try:
            payload = {
                "image_url": "https://example.com/test-image.jpg",
                "prompt": "Camera zooms in slowly",
                "duration": 5
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/from_image", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/from_image", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/from_image", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/from_image", "POST", False, error=str(e))

    def test_text_overlay(self):
        """Test text overlay endpoints."""
        print("\n📝 Testing Text Overlay Endpoints...")

        # Test POST /modern-text-overlay
        try:
            payload = {
                "video_url": "https://example.com/test-video.mp4",
                "text": "Sample Text Overlay",
                "position": "center",
                "font_size": 48,
                "color": "#FFFFFF",
                "background_color": "#000000",
                "duration": 5
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/modern-text-overlay", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/modern-text-overlay", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/modern-text-overlay", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/modern-text-overlay", "POST", False, error=str(e))

        # Test GET /modern-presets - Get modern text overlay presets
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/modern-presets")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/modern-presets", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/modern-presets", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/modern-presets", "GET", False, error=str(e))

        # Test POST /modern-preset/{preset_name} - Apply modern preset
        try:
            payload = {
                "video_url": "https://example.com/test-video.mp4",
                "text": "Preset Text Overlay"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/modern-preset/default", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/modern-preset/{preset_name}", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/modern-preset/{preset_name}", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/modern-preset/{preset_name}", "POST", False, error=str(e))

        # Test POST /preview - Preview text overlay
        try:
            payload = {
                "video_url": "https://example.com/test-video.mp4",
                "text": "Preview Text",
                "position": "bottom",
                "font_size": 36
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/preview", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/preview", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/preview", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/preview", "POST", False, error=str(e))

        # Test GET /all-presets - Get all text overlay presets
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/all-presets")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/all-presets", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/all-presets", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/all-presets", "GET", False, error=str(e))

    def test_video_manipulation(self):
        """Test video manipulation endpoints."""
        print("\n🎞️ Testing Video Manipulation Endpoints...")

        # Test POST /concatenate
        try:
            payload = {
                "video_urls": [
                    "https://example.com/video1.mp4",
                    "https://example.com/video2.mp4"
                ],
                "output_filename": "concatenated_video.mp4"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/concatenate", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/videos/concatenate", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/concatenate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/concatenate", "POST", False, error=str(e))

        # Test POST /add-audio
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "audio_url": "https://example.com/audio.mp3"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/add-audio", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/videos/add-audio", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/add-audio", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/add-audio", "POST", False, error=str(e))

        # Test POST /add-captions
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "srt_url": "https://example.com/captions.srt"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/add-captions", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/add-captions", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/add-captions", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/add-captions", "POST", False, error=str(e))

    def test_video_utilities(self):
        """Test video utility endpoints."""
        print("\n🛠️ Testing Video Utility Endpoints...")

        # Test POST /thumbnails
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "timestamps": [1, 5, 10]
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/thumbnails", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/thumbnails", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/thumbnails", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/thumbnails", "POST", False, error=str(e))

        # Test POST /frames
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "frame_number": 30
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/frames", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/videos/frames", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/frames", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/frames", "POST", False, error=str(e))

        # Test POST /clips
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "start_time": 10,
                "end_time": 20
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/clips", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/clips", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/clips", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/clips", "POST", False, error=str(e))

    def test_video_management(self):
        """Test video management endpoints."""
        print("\n📁 Testing Video Management Endpoints...")

        # Test GET /videos - List videos
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/", "GET", False, error=str(e))

        # Test GET /videos/stats/overview - Video statistics
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/stats/overview")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/stats/overview", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/stats/overview", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/stats/overview", "GET", False, error=str(e))

        # Test GET /videos/{video_id} - Get specific video (using a dummy ID)
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/test-video-id")
            # This might return 404 for non-existent video, which is expected
            if response.status_code in [200, 404]:
                success = response.status_code == 200
                self.log_test_result("/api/v1/videos/{video_id}", "GET", success, response.json() if success else None, 
                                   error=f"Status {response.status_code}: {response.text}" if not success else None)
            else:
                self.log_test_result("/api/v1/videos/{video_id}", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/{video_id}", "GET", False, error=str(e))

        # Test PUT /videos/{video_id} - Update video (using a dummy ID)
        try:
            payload = {
                "title": "Updated Test Video",
                "description": "Updated description"
            }
            response = self.session.put(f"{self.base_url}/api/v1/videos/test-video-id", json=payload)
            # This might return 404 for non-existent video, which is expected
            if response.status_code in [200, 404]:
                success = response.status_code == 200
                self.log_test_result("/api/v1/videos/{video_id}", "PUT", success, response.json() if success else None,
                                   error=f"Status {response.status_code}: {response.text}" if not success else None)
            else:
                self.log_test_result("/api/v1/videos/{video_id}", "PUT", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/{video_id}", "PUT", False, error=str(e))

        # Test DELETE /videos/{video_id} - Delete video (using a dummy ID)
        try:
            response = self.session.delete(f"{self.base_url}/api/v1/videos/test-video-id")
            # This might return 404 for non-existent video, which is expected
            if response.status_code in [200, 204, 404]:
                success = response.status_code in [200, 204]
                self.log_test_result("/api/v1/videos/{video_id}", "DELETE", success, None,
                                   error=f"Status {response.status_code}: {response.text}" if not success else None)
            else:
                self.log_test_result("/api/v1/videos/{video_id}", "DELETE", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/{video_id}", "DELETE", False, error=str(e))

        # Test GET /videos/{video_id}/download - Download video (using a dummy ID)
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/test-video-id/download")
            # This might return 404 for non-existent video, which is expected
            if response.status_code in [200, 404]:
                success = response.status_code == 200
                self.log_test_result("/api/v1/videos/{video_id}/download", "GET", success, None,
                                   error=f"Status {response.status_code}: {response.text}" if not success else None)
            else:
                self.log_test_result("/api/v1/videos/{video_id}/download", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/{video_id}/download", "GET", False, error=str(e))

    def test_caption_styles(self):
        """Test caption styles endpoints."""
        print("\n🎨 Testing Caption Styles Endpoints...")

        # Test GET /videos/caption-styles/presets - Get caption style presets
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/caption-styles/presets")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/caption-styles/presets", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/caption-styles/presets", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/caption-styles/presets", "GET", False, error=str(e))

        # Test GET /videos/caption-styles/presets/{style_name} - Get specific preset
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/caption-styles/presets/default")
            if response.status_code in [200, 404]:
                success = response.status_code == 200
                self.log_test_result("/api/v1/videos/caption-styles/presets/{style_name}", "GET", success, response.json() if success else None,
                                   error=f"Status {response.status_code}: {response.text}" if not success else None)
            else:
                self.log_test_result("/api/v1/videos/caption-styles/presets/{style_name}", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/caption-styles/presets/{style_name}", "GET", False, error=str(e))

        # Test POST /videos/caption-styles/apply-preset - Apply caption style preset
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "preset_name": "default",
                "text": "Sample caption text"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/caption-styles/apply-preset", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/caption-styles/apply-preset", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/caption-styles/apply-preset", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/caption-styles/apply-preset", "POST", False, error=str(e))

        # Test GET /videos/caption-styles/recommendations - Get style recommendations
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/caption-styles/recommendations")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/caption-styles/recommendations", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/caption-styles/recommendations", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/caption-styles/recommendations", "GET", False, error=str(e))

        # Test GET /videos/caption-styles/best-practices - Get caption best practices
        try:
            response = self.session.get(f"{self.base_url}/api/v1/videos/caption-styles/best-practices")
            if response.status_code == 200:
                self.log_test_result("/api/v1/videos/caption-styles/best-practices", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/caption-styles/best-practices", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/caption-styles/best-practices", "GET", False, error=str(e))

    def test_advanced_video(self):
        """Test advanced video endpoints."""
        print("\n⚡ Testing Advanced Video Endpoints...")

        # Test POST /advanced/colorkey-overlay
        try:
            payload = {
                "video_url": "https://example.com/video.mp4",
                "overlay_video_url": "https://example.com/overlay.mp4",
                "color_key": "#00FF00"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/advanced/colorkey-overlay", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/advanced/colorkey-overlay", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/advanced/colorkey-overlay", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/advanced/colorkey-overlay", "POST", False, error=str(e))

    def run_all_tests(self):
        """Run all video endpoint tests."""
        print("🚀 Starting Video Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")

        # Run all test categories
        self.test_video_generation()
        self.test_video_from_image()
        self.test_text_overlay()
        self.test_video_manipulation()
        self.test_video_utilities()
        self.test_video_management()
        self.test_caption_styles()
        self.test_advanced_video()

        # Print summary
        print(f"\n📊 Test Summary:")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")

        if failed_tests > 0:
            print("   ❌ Failed endpoints:")
            for result in self.test_results:
                if not result['success']:
                    print(f"      - {result['method']} {result['endpoint']}: {result['error']}")

        # Save results to file
        output_file = "temp/test_results/video_test_results.json"
        os.makedirs("temp/test_results", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "category": "video",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "results": self.test_results
            }, f, indent=2)

        print(f"   📄 Results saved to: {output_file}")

        return failed_tests == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test video endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = VideoEndpointTester(args.base_url, args.api_key)
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()