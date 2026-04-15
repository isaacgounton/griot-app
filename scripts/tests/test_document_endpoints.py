#!/usr/bin/env python3
"""
Test script for all document endpoints in the Griot.

This script tests all document-related endpoints to ensure they are working correctly.
It covers document processing, language extraction, and format conversion.

Usage:
    python test_document_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

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
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the FastAPI app
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from app.main import app
    client = TestClient(app)
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print("Make sure you're running this from the project root and all dependencies are installed")
    sys.exit(1)


class DocumentEndpointTester:
    """Test class for document endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('API_KEY')
        self.client = client
        self.test_results = []

        if not self.api_key:
            raise ValueError("API_KEY environment variable or --api-key parameter is required")

        # Set default headers for the test client
        self.client.headers.update({
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

    def test_marker_endpoints(self):
        """Test marker document processing endpoints."""
        print("\n📄 Testing Marker Document Processing...")

        # Test POST /marker/
        try:
            payload = {
                "url": "https://example.com/document.pdf",
                "output_format": "markdown"
            }
            response = self.client.post("/api/v1/marker/", json=payload)
            if response.status_code in [200, 201, 400]:
                self.log_test_result("/api/v1/marker/", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/marker/", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/marker/", "POST", False, error=str(e))

        # Test GET /marker/formats
        try:
            response = self.client.get("/api/v1/marker/formats")
            if response.status_code == 200:
                self.log_test_result("/api/v1/marker/formats", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/marker/formats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/marker/formats", "GET", False, error=str(e))

    def test_markdown_conversion(self):
        """Test markdown conversion endpoints."""
        print("\n📝 Testing Markdown Conversion...")

        # Test GET /to-markdown/formats
        try:
            response = self.client.get("/api/v1/to-markdown/formats")
            if response.status_code == 200:
                self.log_test_result("/api/v1/to-markdown/formats", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/to-markdown/formats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/to-markdown/formats", "GET", False, error=str(e))

        # Test POST /to-markdown/to-markdown
        try:
            payload = {
                "url": "https://example.com/document.pdf",
                "output_format": "markdown"
            }
            response = self.client.post("/api/v1/to-markdown/to-markdown", json=payload)
            if response.status_code in [200, 201, 400]:
                self.log_test_result("/api/v1/to-markdown/to-markdown", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/to-markdown/to-markdown", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/to-markdown/to-markdown", "POST", False, error=str(e))

    def test_language_extraction(self):
        """Test language extraction endpoints."""
        print("\n🌍 Testing Language Extraction...")

        # Test GET /langextract/models
        try:
            response = self.client.get("/api/v1/langextract/models")
            if response.status_code == 200:
                self.log_test_result("/api/v1/langextract/models", "GET", True, response.json())
            else:
                self.log_test_result("/api/v1/langextract/models", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/langextract/models", "GET", False, error=str(e))

        # Test POST /langextract
        try:
            payload = {
                "file_url": "https://example.com/document.pdf",
                "extract_images": False,
                "force_ocr": False
            }
            response = self.client.post("/api/v1/langextract", json=payload)
            if response.status_code in [200, 201, 202, 400]:
                self.log_test_result("/api/v1/langextract", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/langextract", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/langextract", "POST", False, error=str(e))

        # Test POST /langextract/json
        try:
            payload = {
                "input_text": "John Doe works at Acme Corp in New York.",
                "sync": True
            }
            response = self.client.post("/api/v1/langextract/json", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/api/v1/langextract/json", "POST", True, response.json())
            else:
                self.log_test_result("/api/v1/langextract/json", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/api/v1/langextract/json", "POST", False, error=str(e))

    def run_all_tests(self):
        """Run all document endpoint tests."""
        print("🚀 Starting Document Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")

        # Run all test categories
        self.test_marker_endpoints()
        self.test_markdown_conversion()
        self.test_language_extraction()

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
        output_file = "temp/test_results/document_test_results.json"
        os.makedirs("temp/test_results", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "category": "document",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "results": self.test_results
            }, f, indent=2)

        print(f"   📄 Results saved to: {output_file}")

        return failed_tests == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test document endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = DocumentEndpointTester(args.base_url, args.api_key)
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