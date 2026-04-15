#!/usr/bin/env python3
"""
Test script for all document endpoints in the Griot.

This script tests all document-related endpoints including conversion, format support,
language extraction, and markdown conversion.

Usage:
    python test_documents_endpoints.py [--base-url BASE_URL] [--api-key API_KEY]

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

class DocumentEndpointTester:
    """Test class for document endpoints."""

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
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {method} {endpoint}")
        if error:
            print(f"   Error: {error}")

    def test_document_conversion(self):
        """Test document conversion endpoints."""
        print("\n📄 Testing Document Conversion Endpoints...")

        # Test POST / - Document conversion with Marker
        try:
            # Create a simple test document payload
            payload = {
                "document_url": "https://example.com/test-document.pdf",
                "output_format": "markdown",
                "options": {
                    "extract_images": True,
                    "table_extraction": True
                }
            }
            response = self.session.post(f"{self.base_url}/", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/", "POST", True, response.json())
            else:
                self.log_test_result("/", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/", "POST", False, error=str(e))

    def test_document_formats(self):
        """Test document format support endpoints."""
        print("\n📋 Testing Document Format Support Endpoints...")

        # Test GET /formats - Get supported formats
        try:
            response = self.session.get(f"{self.base_url}/formats")
            if response.status_code == 200:
                self.log_test_result("/formats", "GET", True, response.json())
            else:
                self.log_test_result("/formats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/formats", "GET", False, error=str(e))

        # Test GET /v1/documents/formats - Get comprehensive formats
        try:
            response = self.session.get(f"{self.base_url}/v1/documents/formats")
            if response.status_code == 200:
                self.log_test_result("/v1/documents/formats", "GET", True, response.json())
            else:
                self.log_test_result("/v1/documents/formats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/v1/documents/formats", "GET", False, error=str(e))

    def test_language_extraction(self):
        """Test language extraction endpoints."""
        print("\n🧠 Testing Language Extraction Endpoints...")

        # Test POST /v1/documents/langextract - Extract structured data
        try:
            payload = {
                "text": "John Doe works at Acme Corp and earns $75,000 annually. Contact: john.doe@acme.com",
                "extraction_type": "entities",
                "model": "gpt-4"
            }
            response = self.session.post(f"{self.base_url}/v1/documents/langextract", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/v1/documents/langextract", "POST", True, response.json())
            else:
                self.log_test_result("/v1/documents/langextract", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/v1/documents/langextract", "POST", False, error=str(e))

        # Test POST /v1/documents/langextract/json - Extract with JSON format
        try:
            payload = {
                "content": {
                    "text": "The meeting is scheduled for March 15th, 2024 at 2:00 PM in Conference Room A.",
                    "metadata": {
                        "source": "email",
                        "priority": "high"
                    }
                },
                "schema": {
                    "date": "string",
                    "time": "string",
                    "location": "string",
                    "priority": "string"
                }
            }
            response = self.session.post(f"{self.base_url}/v1/documents/langextract/json", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/v1/documents/langextract/json", "POST", True, response.json())
            else:
                self.log_test_result("/v1/documents/langextract/json", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/v1/documents/langextract/json", "POST", False, error=str(e))

    def test_language_extraction_models(self):
        """Test language extraction model information endpoints."""
        print("\n🤖 Testing Language Extraction Models Endpoints...")

        # Test GET /v1/documents/langextract/models - Get supported models
        try:
            response = self.session.get(f"{self.base_url}/v1/documents/langextract/models")
            if response.status_code == 200:
                self.log_test_result("/v1/documents/langextract/models", "GET", True, response.json())
            else:
                self.log_test_result("/v1/documents/langextract/models", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/v1/documents/langextract/models", "GET", False, error=str(e))

    def test_markdown_conversion(self):
        """Test markdown conversion endpoints."""
        print("\n📝 Testing Markdown Conversion Endpoints...")

        # Test POST /v1/documents/to-markdown - Convert to markdown
        try:
            payload = {
                "document_url": "https://example.com/test-document.docx",
                "options": {
                    "include_images": True,
                    "preserve_formatting": True,
                    "extract_tables": True
                }
            }
            response = self.session.post(f"{self.base_url}/v1/documents/to-markdown", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/v1/documents/to-markdown", "POST", True, response.json())
            else:
                self.log_test_result("/v1/documents/to-markdown", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/v1/documents/to-markdown", "POST", False, error=str(e))

    def run_all_tests(self):
        """Run all document endpoint tests."""
        print("🚀 Starting Document Endpoints Testing...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")
        print("=" * 60)

        # Run all test categories
        self.test_document_conversion()
        self.test_document_formats()
        self.test_language_extraction()
        self.test_language_extraction_models()
        self.test_markdown_conversion()

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

    def save_results(self):
        """Save test results to file."""
        os.makedirs("temp/test_results", exist_ok=True)
        results_file = "temp/test_results/documents_test_results.json"

        with open(results_file, 'w') as f:
            json.dump({
                'test_run_timestamp': datetime.now().isoformat(),
                'category': 'documents',
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r['success']]),
                'failed_tests': len([r for r in self.test_results if not r['success']]),
                'results': self.test_results
            }, f, indent=2)

        print(f"\n💾 Results saved to {results_file}")

    def print_summary(self):
        """Print test summary."""
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['success']])
        failed = total - passed

        print("\n" + "=" * 60)
        print("📊 DOCUMENTS ENDPOINTS TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(".1f")
        print("=" * 60)

        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['method']} {result['endpoint']}: {result['error']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test document endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = DocumentEndpointTester(base_url=args.base_url, api_key=args.api_key)
        tester.run_all_tests()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()