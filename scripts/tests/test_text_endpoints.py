#!/usr/bin/env python3
"""
Test script for all text endpoints in the Griot.

This script tests all text-related endpoints to ensure they are working correctly.
It covers text generation, script generation, image prompts, topic discovery, and Pollinations.AI text services.

Usage:
    python test_text_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

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

class TextEndpointTester:
    """Test class for text endpoints."""

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

    def test_text_generation(self):
        """Test text generation endpoints."""
        print("\n📝 Testing Text Generation Endpoints...")

        # Test POST /api/v1/text/generate - General text generation
        try:
            payload = {
                "prompt": "Write a short story about a robot learning to paint",
                "max_tokens": 200,
                "temperature": 0.7
            }
            response = self.session.post(f"{self.base_url}/api/v1/text/generate", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/text/generate", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/text/generate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/text/generate", "POST", False, error=str(e))

        # Test POST /api/v1/text/generate/script - Script generation
        try:
            payload = {
                "topic": "The future of artificial intelligence",
                "script_type": "educational",
                "language": "en",
                "max_duration": 300,
                "style": "engaging",
                "target_audience": "general public"
            }
            response = self.session.post(f"{self.base_url}/api/v1/text/generate/script", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/v1/text/generate/script", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/text/generate/script", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/text/generate/script", "POST", False, error=str(e))

        # Test POST /api/v1/text/generate/image-prompt - Image prompt generation
        try:
            payload = {
                "topic": "A serene mountain landscape at sunset",
                "style": "photorealistic",
                "mood": "peaceful",
                "context": "for a travel blog post"
            }
            response = self.session.post(f"{self.base_url}/api/v1/text/generate/image-prompt", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/text/generate/image-prompt", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/text/generate/image-prompt", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/text/generate/image-prompt", "POST", False, error=str(e))

        # Test POST /api/v1/text/discover/topics - Topic discovery
        try:
            payload = {
                "keywords": "artificial intelligence machine learning healthcare education transportation",
                "category": "technology",
                "language": "en",
                "max_results": 5
            }
            response = self.session.post(f"{self.base_url}/api/v1/text/discover/topics", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/text/discover/topics", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/text/discover/topics", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/text/discover/topics", "POST", False, error=str(e))

    def test_pollinations_text(self):
        """Test Pollinations.AI text endpoints."""
        print("\n🌸 Testing Pollinations.AI Text Endpoints...")

        # Test POST /api/pollinations/text/generate - Pollinations text generation
        try:
            payload = {
                "prompt": "Explain quantum computing in simple terms",
                "model": "openai",
                "seed": 42
            }
            response = self.session.post(f"{self.base_url}/api/pollinations/text/generate", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/pollinations/text/generate", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/text/generate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/text/generate", "POST", False, error=str(e))

        # Test POST /api/pollinations/chat/completions - Pollinations chat completions
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": "openai",
                "stream": False
            }
            response = self.session.post(f"{self.base_url}/api/pollinations/chat/completions", json=payload)
            if response.status_code in [200, 201, 202]:  # 202 = Accepted (async job)
                self.log_test_result("/api/pollinations/chat/completions", "POST", True, response.json())
            else:
                self.log_test_result("/api/pollinations/chat/completions", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/pollinations/chat/completions", "POST", False, error=str(e))

    def run_all_tests(self):
        """Run all text endpoint tests."""
        print("🚀 Starting Text Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")

        # Run all test categories
        self.test_text_generation()
        self.test_pollinations_text()

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
        output_file = "temp/test_results/text_test_results.json"
        os.makedirs("temp/test_results", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "category": "text",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "results": self.test_results
            }, f, indent=2)

        print(f"   📄 Results saved to: {output_file}")

        return failed_tests == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test text endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = TextEndpointTester(args.base_url, args.api_key)
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
