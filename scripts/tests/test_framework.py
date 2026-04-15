#!/usr/bin/env python3
"""
Testing Framework for API Endpoints

Provides base classes and utilities for testing FastAPI endpoints
with authentication, async support, and comprehensive result reporting.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single endpoint test."""
    endpoint_path: str
    method: str
    status_code: Optional[int]
    success: bool
    error_message: Optional[str]
    response_time: float
    expected_status: Optional[int]
    response_data: Optional[Any] = None


@dataclass
class CategoryTestResults:
    """Results for a category of endpoint tests."""
    category: str
    total_endpoints: int
    successful_tests: int
    failed_tests: int
    execution_time: float
    results: List[TestResult]


class EndpointTester:
    """Base class for testing API endpoints."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[TestResult] = []

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
            headers['Content-Type'] = 'application/json'

        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_endpoint(
        self,
        path: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        expected_status: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> TestResult:
        """Test a single endpoint."""
        if not self.session:
            raise RuntimeError("EndpointTester must be used as async context manager")

        start_time = time.time()
        url = f"{self.base_url}{path}"
        success = False
        status_code = None
        error_message = None
        response_data = None

        try:
            # Prepare request
            request_kwargs = {}
            if data:
                request_kwargs['json'] = data
            if headers:
                request_kwargs['headers'] = headers

            # Make request
            async with self.session.request(method.upper(), url, **request_kwargs) as response:
                status_code = response.status
                response_time = time.time() - start_time

                # Check if status matches expectation
                if expected_status:
                    success = status_code == expected_status
                else:
                    # Default success criteria
                    success = status_code < 400

                # Get response data for successful requests
                if success and response.content_type == 'application/json':
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                elif not success:
                    try:
                        error_data = await response.json()
                        error_message = json.dumps(error_data, indent=2)
                    except:
                        error_message = await response.text()

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            error_message = f"Request timeout after {self.timeout}s"
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            error_message = f"Client error: {str(e)}"
        except Exception as e:
            response_time = time.time() - start_time
            error_message = f"Unexpected error: {str(e)}"

        result = TestResult(
            endpoint_path=path,
            method=method.upper(),
            status_code=status_code,
            success=success,
            error_message=error_message,
            response_time=response_time,
            expected_status=expected_status,
            response_data=response_data
        )

        self.test_results.append(result)
        return result

    def get_test_summary(self) -> CategoryTestResults:
        """Get summary of all test results."""
        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r.success)
        failed = total - successful

        # Calculate total execution time
        execution_time = sum(r.response_time for r in self.test_results)

        return CategoryTestResults(
            category=self.__class__.__name__.replace('Tester', '').lower(),
            total_endpoints=total,
            successful_tests=successful,
            failed_tests=failed,
            execution_time=execution_time,
            results=self.test_results
        )


class AsyncEndpointTester(EndpointTester):
    """Extended tester with additional async utilities."""

    async def test_endpoints_parallel(
        self,
        endpoints: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[TestResult]:
        """Test multiple endpoints in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def test_with_semaphore(endpoint_config: Dict[str, Any]) -> TestResult:
            async with semaphore:
                return await self.test_endpoint(**endpoint_config)

        tasks = [test_with_semaphore(config) for config in endpoints]
        return await asyncio.gather(*tasks)

    async def wait_for_job_completion(
        self,
        job_id: str,
        status_endpoint: str,
        max_attempts: int = 30,
        delay: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Wait for an async job to complete."""
        for attempt in range(max_attempts):
            result = await self.test_endpoint(
                f"{status_endpoint}/{job_id}",
                method="GET"
            )

            if result.success and result.response_data:
                status = result.response_data.get('status', '').lower()
                if status == 'completed':
                    return result.response_data
                elif status == 'failed':
                    raise Exception(f"Job {job_id} failed: {result.response_data}")

            await asyncio.sleep(delay)

        raise Exception(f"Job {job_id} did not complete within {max_attempts * delay} seconds")


def save_test_results(results: CategoryTestResults, output_file: str) -> None:
    """Save test results to a JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = asdict(results)
    # Convert datetime objects to ISO strings
    data['timestamp'] = datetime.now().isoformat()

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"📄 Test results saved to: {output_path}")


def print_test_summary(results: CategoryTestResults) -> None:
    """Print a formatted test summary."""
    print(f"\n🧪 {results.category.title()} Endpoint Test Results:")
    print(f"   Total: {results.total_endpoints}")
    print(f"   Passed: {results.successful_tests}")
    print(f"   Failed: {results.failed_tests}")
    print(".2f"
    if results.failed_tests > 0:
        print("   ❌ Failed endpoints:")
        for result in results.results:
            if not result.success:
                print(f"      - {result.method} {result.endpoint_path}: {result.error_message}")


# Utility functions for common test patterns
def create_job_test_payload(**kwargs) -> Dict[str, Any]:
    """Create a standard job test payload."""
    return {
        "test_mode": True,
        **kwargs
    }


def validate_job_response(response_data: Dict[str, Any]) -> bool:
    """Validate that a response contains expected job fields."""
    required_fields = ['job_id', 'status']
    return all(field in response_data for field in required_fields)


def validate_success_response(response_data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate that a success response contains required fields."""
    return all(field in response_data for field in required_fields)