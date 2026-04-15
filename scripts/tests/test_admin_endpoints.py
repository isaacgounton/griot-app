#!/usr/bin/env python3
"""
Admin Endpoints Testing Script
Tests all admin-related endpoints including authentication, user management, job management, and system status.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestResult:
    """Result of a single endpoint test."""
    def __init__(self, endpoint: str, method: str, success: bool, response_data: Any = None, error: str = None):
        self.endpoint = endpoint
        self.method = method
        self.success = success
        self.response_data = response_data
        self.error = error
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "success": self.success,
            "response_data": self.response_data,
            "error": self.error,
            "timestamp": self.timestamp
        }

class BaseEndpointTest:
    """Base class for endpoint testing"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    def test_endpoint(self, name: str, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None, expected_status: int = 200,
                     content_type: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> TestResult:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"

            # Prepare headers
            request_headers = {"Content-Type": "application/json"}
            if self.api_key:
                request_headers["X-API-Key"] = self.api_key
            if headers:
                request_headers.update(headers)

            # Make request
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, params=params, timeout=30)
            else:
                return TestResult(name, method, False, error=f"Unsupported method: {method}")

            # Check status
            success = response.status_code == expected_status

            # Check content type if specified
            if content_type and success:
                actual_content_type = response.headers.get('content-type', '')
                if content_type not in actual_content_type:
                    success = False
                    response._content = f"Wrong content type: expected {content_type}, got {actual_content_type}".encode()

            response_data = None
            if response.content:
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                    else:
                        response_data = response.text
                except:
                    response_data = response.text

            if not success:
                error = f"Status {response.status_code}: {response_data}"
                return TestResult(name, method, False, response_data, error)

            return TestResult(name, method, True, response_data)

        except requests.exceptions.RequestException as e:
            return TestResult(name, method, False, error=f"Request failed: {str(e)}")
        except Exception as e:
            return TestResult(name, method, False, error=f"Unexpected error: {str(e)}")

    def save_results(self, summary: Dict[str, Any], filename: str):
        """Save test results to file"""
        os.makedirs("temp/test_results", exist_ok=True)
        filepath = f"temp/test_results/{filename}"
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

class AdminEndpointsTest(BaseEndpointTest):
    """Test class for admin endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        super().__init__(base_url, api_key)
        self.admin_token = None
        self.test_user_id = None

    def login_admin(self) -> bool:
        """Login as admin and store token for subsequent requests"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            response = requests.post(f"{self.base_url}/admin/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.admin_token = data["token"]
                    return True
            return False
        except Exception as e:
            return False

    def test_admin_authentication(self) -> List[TestResult]:
        """Test admin authentication endpoints"""
        results = []

        # Test admin login page (GET)
        results.append(self.test_endpoint(
            "GET /admin",
            "GET",
            "/admin",
            expected_status=200,
            content_type="text/html"
        ))

        # Test admin login (POST)
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        results.append(self.test_endpoint(
            "POST /admin/login",
            "POST",
            "/admin/login",
            data=login_data,
            expected_status=200
        ))

        # Test admin verification
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            results.append(self.test_endpoint(
                "GET /admin/verify",
                "GET",
                "/admin/verify",
                headers=headers,
                expected_status=200
            ))

        # Test admin logout
        results.append(self.test_endpoint(
            "GET /admin/logout",
            "GET",
            "/admin/logout",
            expected_status=200,
            content_type="text/html"
        ))

        return results

    def test_admin_dashboard(self) -> List[TestResult]:
        """Test admin dashboard endpoints"""
        results = []

        # Test admin dashboard page
        results.append(self.test_endpoint(
            "GET /admin/dashboard",
            "GET",
            "/admin/dashboard",
            expected_status=200,
            content_type="text/html"
        ))

        # Test admin stats (requires authentication)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        results.append(self.test_endpoint(
            "GET /admin/stats",
            "GET",
            "/admin/stats",
            headers=headers,
            expected_status=200
        ))

        # Test admin jobs overview
        results.append(self.test_endpoint(
            "GET /admin/jobs",
            "GET",
            "/admin/jobs",
            headers=headers,
            expected_status=200
        ))

        # Test admin system info
        results.append(self.test_endpoint(
            "GET /admin/system",
            "GET",
            "/admin/system",
            headers=headers,
            expected_status=200
        ))

        return results

    def test_user_management(self) -> List[TestResult]:
        """Test user management endpoints"""
        results = []
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        # Test create user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "testpass123",
            "role": "user",
            "is_active": True
        }
        create_result = self.test_endpoint(
            "POST /api/admin/users/",
            "POST",
            "/api/admin/users/",
            data=user_data,
            headers=headers,
            expected_status=200
        )
        results.append(create_result)

        # Extract user ID if creation was successful
        if create_result.success and create_result.response_data:
            try:
                user_response = json.loads(create_result.response_data) if isinstance(create_result.response_data, str) else create_result.response_data
                if isinstance(user_response, dict) and "id" in user_response:
                    self.test_user_id = user_response["id"]
            except:
                pass

        # Test list users
        results.append(self.test_endpoint(
            "GET /api/admin/users/",
            "GET",
            "/api/admin/users/",
            headers=headers,
            expected_status=200
        ))

        # Test user stats
        results.append(self.test_endpoint(
            "GET /api/admin/users/stats",
            "GET",
            "/api/admin/users/stats",
            headers=headers,
            expected_status=200
        ))

        # Test get specific user (if we have a user ID)
        if self.test_user_id:
            results.append(self.test_endpoint(
                f"GET /api/admin/users/{self.test_user_id}",
                "GET",
                f"/api/admin/users/{self.test_user_id}",
                headers=headers,
                expected_status=200
            ))

            # Test update user
            update_data = {
                "username": "testuser_updated",
                "email": "test_updated@example.com",
                "full_name": "Test User Updated",
                "role": "user",
                "is_active": True
            }
            results.append(self.test_endpoint(
                f"PUT /api/admin/users/{self.test_user_id}",
                "PUT",
                f"/api/admin/users/{self.test_user_id}",
                data=update_data,
                headers=headers,
                expected_status=200
            ))

            # Test delete user
            results.append(self.test_endpoint(
                f"DELETE /api/admin/users/{self.test_user_id}",
                "DELETE",
                f"/api/admin/users/{self.test_user_id}",
                headers=headers,
                expected_status=204
            ))

        # Test user authentication
        auth_params = {
            "email": "admin@griot.com",
            "password": "admin123"
        }
        results.append(self.test_endpoint(
            "POST /api/admin/users/authenticate",
            "POST",
            "/api/admin/users/authenticate",
            params=auth_params,
            headers=headers,
            expected_status=200
        ))

        return results

    def test_job_management(self) -> List[TestResult]:
        """Test job management endpoints"""
        results = []
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        # Test cleanup configuration
        cleanup_data = {
            "max_age_hours": 24
        }
        results.append(self.test_endpoint(
            "POST /api/admin/jobs/cleanup",
            "POST",
            "/api/admin/jobs/cleanup",
            data=cleanup_data,
            headers=headers,
            expected_status=200
        ))

        # Test cleanup status
        results.append(self.test_endpoint(
            "GET /api/admin/jobs/cleanup/status",
            "GET",
            "/api/admin/jobs/cleanup/status",
            headers=headers,
            expected_status=200
        ))

        # Test trigger cleanup
        results.append(self.test_endpoint(
            "POST /api/admin/jobs/cleanup/trigger",
            "POST",
            "/api/admin/jobs/cleanup/trigger",
            headers=headers,
            expected_status=200
        ))

        # Test job stats
        results.append(self.test_endpoint(
            "GET /api/admin/jobs/stats",
            "GET",
            "/api/admin/jobs/stats",
            headers=headers,
            expected_status=200
        ))

        # Test delete specific job (using a test job ID)
        test_job_id = "test-job-123"
        results.append(self.test_endpoint(
            f"DELETE /api/admin/jobs/{test_job_id}",
            "DELETE",
            f"/api/admin/jobs/{test_job_id}",
            headers=headers,
            expected_status=404  # Expected to fail since job doesn't exist
        ))

        # Test scheduler start
        results.append(self.test_endpoint(
            "POST /api/admin/jobs/scheduler/start",
            "POST",
            "/api/admin/jobs/scheduler/start",
            headers=headers,
            expected_status=200
        ))

        # Test scheduler stop
        results.append(self.test_endpoint(
            "POST /api/admin/jobs/scheduler/stop",
            "POST",
            "/api/admin/jobs/scheduler/stop",
            headers=headers,
            expected_status=200
        ))

        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all admin endpoint tests"""
        print("🚀 Starting Admin Endpoint Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'None'}")
        print("=" * 50)

        all_results = []

        # Try to login as admin first
        print("🔐 Attempting admin login...")
        if self.login_admin():
            print("✅ Admin login successful")
        else:
            print("❌ Admin login failed - some tests may not work")

        # Test categories
        test_categories = [
            ("Admin Authentication", self.test_admin_authentication),
            ("Admin Dashboard", self.test_admin_dashboard),
            ("User Management", self.test_user_management),
            ("Job Management", self.test_job_management),
        ]

        for category_name, test_method in test_categories:
            print(f"\n🔧 Testing {category_name} Endpoints...")
            try:
                results = test_method()
                all_results.extend(results)
                print(f"   Completed {len(results)} tests")
            except Exception as e:
                print(f"   ❌ Error in {category_name}: {str(e)}")

        # Generate summary
        passed = sum(1 for r in all_results if r.success)
        failed = len(all_results) - passed

        summary = {
            "test_run": datetime.now().isoformat(),
            "category": "admin",
            "total_tests": len(all_results),
            "passed_tests": passed,
            "failed_tests": failed,
            "results": [r.to_dict() for r in all_results]
        }

        # Save results
        self.save_results(summary, "admin_test_results.json")

        # Print summary
        print("\n" + "=" * 50)
        print("📊 ADMIN ENDPOINTS TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {len(all_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(".1f")
        print("=" * 50)

        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in all_results:
                if not result.success:
                    print(f"  - {result.endpoint}: {result.error}")

        print(f"\n📄 Results saved to: temp/test_results/admin_test_results.json")

        return summary


def main():
    """Main entry point"""
    # Get API key from environment
    api_key = os.getenv('API_KEY')

    # Create test instance
    tester = AdminEndpointsTest(api_key=api_key)

    # Run tests
    try:
        results = tester.run_all_tests()
        # Exit with error code if any tests failed
        if results['failed_tests'] > 0:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

    def log_result(self, endpoint: str, method: str, success: bool, status_code: int,
                   response_data: Any = None, error: str = None):
        """Log test result."""
        result = {
            'endpoint': endpoint,
            'method': method,
            'success': success,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat(),
            'response': response_data,
            'error': error
        }
        self.test_results.append(result)
        print(f"{'✓' if success else '✗'} {method} {endpoint} - {status_code}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            # Create a mock response for logging
            class MockResponse:
                status_code = 0
                text = str(e)
            return MockResponse()

    def test_admin_login(self):
        """Test admin login endpoint."""
        endpoint = "/admin/login"
        data = {
            "username": self.admin_username,
            "password": self.admin_password
        }

        response = self.make_request("POST", endpoint, json=data)

        if response.status_code == 200:
            try:
                response_data = response.json()
                self.log_result(endpoint, "POST", True, response.status_code, response_data)
                return True
            except (ValueError, json.JSONDecodeError) as e:
                self.log_result(endpoint, "POST", False, response.status_code, error=f"Invalid JSON response: {e}")
                return False
        else:
            self.log_result(endpoint, "POST", False, response.status_code, error=response.text)
            return False

    def test_admin_verify(self):
        """Test admin session verification."""
        endpoint = "/admin/verify"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_stats(self):
        """Test admin stats endpoint."""
        endpoint = "/admin/stats"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs(self):
        """Test admin jobs endpoint."""
        endpoint = "/admin/jobs"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_system(self):
        """Test admin system info endpoint."""
        endpoint = "/admin/system"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs_cleanup_status(self):
        """Test admin jobs cleanup status endpoint."""
        endpoint = "/admin/jobs/cleanup/status"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs_stats(self):
        """Test admin jobs stats endpoint."""
        endpoint = "/admin/jobs/stats"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_users_stats(self):
        """Test admin users stats endpoint."""
        endpoint = "/admin/users/stats"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_users_list(self):
        """Test admin users list endpoint."""
        endpoint = "/admin/users/"
        response = self.make_request("GET", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "GET", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_users_create(self):
        """Test admin users create endpoint."""
        endpoint = "/admin/users/"
        data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "user",
            "is_active": True
        }

        response = self.make_request("POST", endpoint, json=data)

        # This might fail if user already exists, which is expected
        success = response.status_code in [200, 201, 400]  # 400 is OK if user exists
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "POST", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs_cleanup_trigger(self):
        """Test admin jobs cleanup trigger endpoint."""
        endpoint = "/admin/jobs/cleanup/trigger"
        response = self.make_request("POST", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "POST", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs_scheduler_start(self):
        """Test admin jobs scheduler start endpoint."""
        endpoint = "/admin/jobs/scheduler/start"
        response = self.make_request("POST", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "POST", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def test_admin_jobs_scheduler_stop(self):
        """Test admin jobs scheduler stop endpoint."""
        endpoint = "/admin/jobs/scheduler/stop"
        response = self.make_request("POST", endpoint)

        success = response.status_code == 200
        try:
            response_data = response.json() if success else None
        except (ValueError, json.JSONDecodeError):
            response_data = None

        self.log_result(endpoint, "POST", success, response.status_code, response_data,
                       error=response.text if not success else None)
        return success

    def run_all_tests(self):
        """Run all admin endpoint tests."""
        print("🧪 Testing Admin Endpoints")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {self.api_key[:10]}...")
        print()

        # Test basic admin endpoints
        print("📊 Testing Basic Admin Endpoints:")
        self.test_admin_login()
        self.test_admin_verify()
        self.test_admin_stats()
        self.test_admin_jobs()
        self.test_admin_system()

        print("\n🔧 Testing Job Management Endpoints:")
        self.test_admin_jobs_cleanup_status()
        self.test_admin_jobs_stats()
        self.test_admin_jobs_cleanup_trigger()
        self.test_admin_jobs_scheduler_start()
        self.test_admin_jobs_scheduler_stop()

        print("\n👥 Testing User Management Endpoints:")
        self.test_admin_users_stats()
        self.test_admin_users_list()
        self.test_admin_users_create()

        print("\n" + "=" * 50)
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - successful_tests

        print("📋 Test Summary:")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(".1f")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['method']} {result['endpoint']} ({result['status_code']})")
                    if result['error']:
                        print(f"    Error: {result['error'][:100]}...")

        print("\n✅ Test completed!")


def main():
    parser = argparse.ArgumentParser(description="Test admin endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL of the API server")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    # Use API key from environment if not provided via command line
    api_key = args.api_key or os.getenv("API_KEY")
    if not api_key:
        print("❌ Error: API key not provided. Set API_KEY environment variable or use --api-key")
        sys.exit(1)

    try:
        tester = AdminEndpointsTest(args.base_url, api_key)
        tester.run_all_tests()
        print("\n✅ Test completed!")
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()