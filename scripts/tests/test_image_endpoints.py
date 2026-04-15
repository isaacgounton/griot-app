#!/usr/bin/env python3
"""
Test script for all image endpoints in the Griot.

This script tests all image-related endpoints to ensure they are working correctly.
It covers image generation, editing, enhancement, and Pollinations AI endpoints.

Usage:
    python test_image_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

Environment Variables:
    API_KEY: The main API key for authentication
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageEndpointTester:
    """Test class for image endpoints."""

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

    def log_test_result(self, endpoint: str, method: str, success: bool, response_data: Any = None, error: Optional[str] = None):
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

    def test_image_generation(self):
        """Test image generation endpoints."""
        print("\n🎨 Testing Image Generation Endpoints...")

        # Test POST /api/v1/images/generate
        try:
            payload = {
                "prompt": "A beautiful sunset over mountains",
                "width": 512,
                "height": 512,
                "model": "flux"
            }
            response = self.session.post(f"{self.base_url}/api/v1/images/generate", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/images/generate", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/images/generate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/images/generate", "POST", False, error=str(e))

    def test_image_editing(self):
        """Test image editing endpoints."""
        print("\n✏️ Testing Image Editing Endpoints...")

        # Test POST /api/v1/images/edit
        try:
            payload = {
                "base_image_url": "https://example.com/base-image.jpg",
                "overlay_images": [
                    {
                        "url": "https://example.com/overlay-image.jpg",
                        "x": 0.5,
                        "y": 0.5,
                        "width": 0.3,
                        "height": 0.3,
                        "rotation": 0.0,
                        "opacity": 1.0
                    }
                ],
                "output_format": "png",
                "sync": False
            }
            response = self.session.post(f"{self.base_url}/api/v1/images/edit", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/images/edit", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/images/edit", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/images/edit", "POST", False, error=str(e))

    def test_image_enhancement(self):
        """Test image enhancement endpoints."""
        print("\n✨ Testing Image Enhancement Endpoints...")

        # Test POST /api/v1/images/enhance
        try:
            payload = {
                "image_url": "https://example.com/image.jpg",
                "enhancement_type": "upscale"
            }
            response = self.session.post(f"{self.base_url}/api/v1/images/enhance", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/images/enhance", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/images/enhance", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/images/enhance", "POST", False, error=str(e))

    def test_pollinations_image_generation(self):
        """Test Pollinations image generation endpoints."""
        print("\n🌸 Testing Pollinations Image Generation...")

        # Test POST /api/pollinations/image/generate
        try:
            payload = {
                "prompt": "A futuristic city at night",
                "width": 512,
                "height": 512,
                "model": "flux"
            }
            response = self.session.post(f"{self.base_url}/api/pollinations/image/generate", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/pollinations/image/generate", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/image/generate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/image/generate", "POST", False, error=str(e))

    def test_pollinations_vision_analyze(self):
        """Test Pollinations vision analysis endpoints."""
        print("\n👁️ Testing Pollinations Vision Analysis...")

        # Test POST /api/pollinations/vision/analyze
        try:
            payload = {
                "image_url": "https://example.com/image.jpg",
                "prompt": "Describe this image in detail"
            }
            response = self.session.post(f"{self.base_url}/api/pollinations/vision/analyze", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/pollinations/vision/analyze", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/vision/analyze", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/vision/analyze", "POST", False, error=str(e))

    def test_pollinations_models(self):
        """Test Pollinations models endpoints."""
        print("\n🤖 Testing Pollinations Models...")

        # Test GET /api/pollinations/models/image
        try:
            response = self.session.get(f"{self.base_url}/api/pollinations/models/image")
            if response.status_code == 200:
                self.log_test_result("/api/pollinations/models/image", "GET", True, response.json())
            else:
                self.log_test_result("/api/pollinations/models/image", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/models/image", "GET", False, error=str(e))

        # Test GET /api/pollinations/models/text
        try:
            response = self.session.get(f"{self.base_url}/api/pollinations/models/text")
            if response.status_code == 200:
                self.log_test_result("/api/pollinations/models/text", "GET", True, response.json())
            else:
                self.log_test_result("/api/pollinations/models/text", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/models/text", "GET", False, error=str(e))

    def test_image_to_video(self):
        """Test image to video generation endpoints."""
        print("\n🎬 Testing Image to Video Generation...")

        # Test POST /api/v1/videos/generations
        try:
            payload = {
                "image_url": "https://example.com/image.jpg",
                "duration": 5,
                "prompt": "Camera zooms in slowly"
            }
            response = self.session.post(f"{self.base_url}/api/v1/videos/generations", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/videos/generations", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/videos/generations", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/videos/generations", "POST", False, error=str(e))

    def run_all_tests(self):
        """Run all image endpoint tests."""
        print("🚀 Starting Image Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")
        print("=" * 60)

        # Run all test categories
        self.test_image_generation()
        self.test_image_editing()
        self.test_image_enhancement()
        self.test_pollinations_image_generation()
        self.test_pollinations_vision_analyze()
        self.test_pollinations_models()
        self.test_image_to_video()

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print("\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")

        if failed_tests > 0:
            print(f"   ❌ Failed endpoints:")
            for result in self.test_results:
                if not result['success']:
                    print(f"      - {result['endpoint']}: {result['error']}")

        print(f"\n   📄 Results saved to: temp/test_results/image_test_results.json")

    def save_results(self):
        """Save test results to file."""
        os.makedirs("temp/test_results", exist_ok=True)
        results_file = "temp/test_results/image_test_results.json"

        with open(results_file, 'w') as f:
            json.dump({
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "base_url": self.base_url,
                    "total_tests": len(self.test_results),
                    "passed_tests": sum(1 for result in self.test_results if result['success']),
                    "failed_tests": sum(1 for result in self.test_results if not result['success'])
                },
                "results": self.test_results
            }, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Test image endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL of the API server")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = ImageEndpointTester(args.base_url, args.api_key)
        tester.run_all_tests()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()