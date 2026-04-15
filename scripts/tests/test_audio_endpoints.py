#!/usr/bin/env python3
"""
Test script for all audio endpoints in the Griot.

This script tests all audio-related endpoints to ensure they are working correctly.
It covers text-to-speech, music generation, transcription, and Pollinations.AI audio services.

Usage:
    python test_audio_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

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

class AudioEndpointTester:
    """Test class for audio endpoints."""

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

    def test_text_to_speech(self):
        """Test text-to-speech endpoints."""
        print("\n🗣️ Testing Text-to-Speech Endpoints...")

        # Test POST /api/v1/audio/speech - Text to speech conversion
        try:
            payload = {
                "text": "Hello, this is a test of the text to speech system.",
                "voice": "alloy",
                "provider": "kokoro"
            }
            response = self.session.post(f"{self.base_url}/api/v1/audio/speech", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/audio/speech", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/speech", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/speech", "POST", False, error=str(e))

        # Test GET /api/v1/audio/voices - Get available voices
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/voices")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/voices", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/voices", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/voices", "GET", False, error=str(e))

        # Test GET /api/v1/audio/voices/formatted - Get formatted voices
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/voices/formatted")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/voices/formatted", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/voices/formatted", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/voices/formatted", "GET", False, error=str(e))

        # Test GET /api/v1/audio/voices/all - Get all voices
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/voices/all")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/voices/all", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/voices/all", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/voices/all", "GET", False, error=str(e))

        # Test GET /api/v1/audio/models - Get available models
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/models")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/models", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/models", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/models", "GET", False, error=str(e))

        # Test GET /api/v1/audio/providers - Get available providers
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/providers")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/providers", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/providers", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/providers", "GET", False, error=str(e))

    def test_music_generation(self):
        """Test music generation endpoints."""
        print("\n🎵 Testing Music Generation Endpoints...")

        # Test POST /api/v1/audio/music - Music generation
        try:
            payload = {
                "description": "A calm and peaceful piano melody",
                "duration": 30,
                "model": "melody"
            }
            response = self.session.post(f"{self.base_url}/api/v1/audio/music", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/audio/music", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/music", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/music", "POST", False, error=str(e))

        # Test GET /api/v1/audio/music/info - Music generation info
        try:
            response = self.session.get(f"{self.base_url}/api/v1/audio/music/info")
            if response.status_code == 200:
                self.log_test_result("/api/v1/audio/music/info", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/music/info", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/music/info", "GET", False, error=str(e))

    def test_transcription(self):
        """Test transcription endpoints."""
        print("\n📝 Testing Transcription Endpoints...")

        # Test POST /api/v1/audio/transcriptions - Audio transcription
        try:
            payload = {
                "media_url": "https://example.com/test-audio.mp3",
                "language": "en"
            }
            response = self.session.post(f"{self.base_url}/api/v1/audio/transcriptions", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/audio/transcriptions", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/audio/transcriptions", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/audio/transcriptions", "POST", False, error=str(e))

    def test_pollinations_audio(self):
        """Test Pollinations.AI audio endpoints."""
        print("\n🌸 Testing Pollinations.AI Audio Endpoints...")

        # Test POST /api/pollinations/audio/tts - Pollinations TTS
        try:
            payload = {
                "text": "Hello from Pollinations.AI",
                "voice": "alloy"
            }
            response = self.session.post(f"{self.base_url}/api/pollinations/audio/tts", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/pollinations/audio/tts", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/audio/tts", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/audio/tts", "POST", False, error=str(e))

        # Test POST /api/pollinations/audio/transcribe - Pollinations transcription
        try:
            # Note: This endpoint requires file upload, so we'll test with minimal valid parameters
            # In a real test, you'd upload an actual audio file
            payload = {
                "audio_format": "wav",
                "question": "Transcribe this audio",
                "sync": False
            }
            # For file upload endpoints, we can't easily test without actual files
            # This will fail with missing file, but at least tests the parameter validation
            response = self.session.post(f"{self.base_url}/api/pollinations/audio/transcribe", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/pollinations/audio/transcribe", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/audio/transcribe", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/audio/transcribe", "POST", False, error=str(e))

        # Test GET /api/pollinations/voices - Pollinations voices
        try:
            response = self.session.get(f"{self.base_url}/api/pollinations/voices")
            if response.status_code == 200:
                self.log_test_result("/api/pollinations/voices", "GET", True, response.json())
            else:
                self.log_test_result("/api/pollinations/voices", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/voices", "GET", False, error=str(e))

    def run_all_tests(self):
        """Run all audio endpoint tests."""
        print("🚀 Starting Audio Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")

        # Run all test categories
        self.test_text_to_speech()
        self.test_music_generation()
        self.test_transcription()
        self.test_pollinations_audio()

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
        output_file = "temp/test_results/audio_test_results.json"
        os.makedirs("temp/test_results", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "category": "audio",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "results": self.test_results
            }, f, indent=2)

        print(f"   📄 Results saved to: {output_file}")

        return failed_tests == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test audio endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = AudioEndpointTester(args.base_url, args.api_key)
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