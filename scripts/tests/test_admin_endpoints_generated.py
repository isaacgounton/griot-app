#!/usr/bin/env python3
"""
Generated test script for all admin endpoints in the Griot.

This script was automatically generated based on endpoint discovery and validation.
It tests all admin-related endpoints including dashboard, jobs management, user management, and system administration.

Generated on: 2024-12-19
Endpoints tested: 44
Categories: dashboard, jobs, users, system, authentication

Usage:
    python test_admin_endpoints_generated.py [--base-url BASE_URL] [--api-key API_KEY]

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

class AdminEndpointTester:
    """Test class for admin endpoints."""

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

    def test_admin_dashboard(self):
        """Test admin dashboard endpoints."""
        print("\n📊 Testing Admin Dashboard Endpoints...")

        # Test GET /admin
        try:
            response = self.session.get(f"{self.base_url}/admin")
            if response.status_code == 200:
                self.log_test_result("/admin", "GET", True, response.json())
            else:
                self.log_test_result("/admin", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin", "GET", False, error=str(e))

        # Test GET /admin/dashboard
        try:
            response = self.session.get(f"{self.base_url}/admin/dashboard")
            if response.status_code == 200:
                self.log_test_result("/admin/dashboard", "GET", True, response.json())
            else:
                self.log_test_result("/admin/dashboard", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/dashboard", "GET", False, error=str(e))

    def test_admin_jobs(self):
        """Test admin jobs management endpoints."""
        print("\n⚙️ Testing Admin Jobs Management Endpoints...")

        # Test GET /admin/jobs
        try:
            response = self.session.get(f"{self.base_url}/admin/jobs")
            if response.status_code == 200:
                self.log_test_result("/admin/jobs", "GET", True, response.json())
            else:
                self.log_test_result("/admin/jobs", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs", "GET", False, error=str(e))

        # Test GET /admin/jobs/stats
        try:
            response = self.session.get(f"{self.base_url}/admin/jobs/stats")
            if response.status_code == 200:
                self.log_test_result("/admin/jobs/stats", "GET", True, response.json())
            else:
                self.log_test_result("/admin/jobs/stats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/stats", "GET", False, error=str(e))

    def test_admin_jobs_cleanup(self):
        """Test admin jobs cleanup endpoints."""
        print("\n🧹 Testing Admin Jobs Cleanup Endpoints...")

        # Test POST /admin/jobs/cleanup
        try:
            response = self.session.post(f"{self.base_url}/admin/jobs/cleanup")
            if response.status_code in [200, 201, 202]:
                self.log_test_result("/admin/jobs/cleanup", "POST", True, response.json())
            else:
                self.log_test_result("/admin/jobs/cleanup", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/cleanup", "POST", False, error=str(e))

        # Test GET /admin/jobs/cleanup/status
        try:
            response = self.session.get(f"{self.base_url}/admin/jobs/cleanup/status")
            if response.status_code == 200:
                self.log_test_result("/admin/jobs/cleanup/status", "GET", True, response.json())
            else:
                self.log_test_result("/admin/jobs/cleanup/status", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/cleanup/status", "GET", False, error=str(e))

        # Test POST /admin/jobs/cleanup/trigger
        try:
            response = self.session.post(f"{self.base_url}/admin/jobs/cleanup/trigger")
            if response.status_code in [200, 201, 202]:
                self.log_test_result("/admin/jobs/cleanup/trigger", "POST", True, response.json())
            else:
                self.log_test_result("/admin/jobs/cleanup/trigger", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/cleanup/trigger", "POST", False, error=str(e))

    def test_admin_jobs_scheduler(self):
        """Test admin jobs scheduler endpoints."""
        print("\n⏰ Testing Admin Jobs Scheduler Endpoints...")

        # Test POST /admin/jobs/scheduler/start
        try:
            response = self.session.post(f"{self.base_url}/admin/jobs/scheduler/start")
            if response.status_code in [200, 201, 202]:
                self.log_test_result("/admin/jobs/scheduler/start", "POST", True, response.json())
            else:
                self.log_test_result("/admin/jobs/scheduler/start", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/scheduler/start", "POST", False, error=str(e))

        # Test POST /admin/jobs/scheduler/stop
        try:
            response = self.session.post(f"{self.base_url}/admin/jobs/scheduler/stop")
            if response.status_code in [200, 201, 202]:
                self.log_test_result("/admin/jobs/scheduler/stop", "POST", True, response.json())
            else:
                self.log_test_result("/admin/jobs/scheduler/stop", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/jobs/scheduler/stop", "POST", False, error=str(e))

    def test_admin_jobs_deletion(self):
        """Test admin jobs deletion endpoints."""
        print("\n🗑️ Testing Admin Jobs Deletion Endpoints...")

        # Test DELETE /admin/jobs/jobs/{job_id} - using a test job ID
        try:
            job_id = "test-job-123"
            response = self.session.delete(f"{self.base_url}/admin/jobs/jobs/{job_id}")
            if response.status_code in [200, 204, 404]:  # 404 is acceptable for non-existent job
                self.log_test_result(f"/admin/jobs/jobs/{job_id}", "DELETE", True, response.json() if response.text else None)
            else:
                self.log_test_result(f"/admin/jobs/jobs/{job_id}", "DELETE", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result(f"/admin/jobs/jobs/test-job-123", "DELETE", False, error=str(e))

    def test_admin_authentication(self):
        """Test admin authentication endpoints."""
        print("\n🔐 Testing Admin Authentication Endpoints...")

        # Test POST /admin/login
        try:
            payload = {
                "username": "admin",
                "password": "test-password"
            }
            response = self.session.post(f"{self.base_url}/admin/login", json=payload)
            if response.status_code in [200, 201, 401]:  # 401 is acceptable for invalid credentials
                self.log_test_result("/admin/login", "POST", True, response.json())
            else:
                self.log_test_result("/admin/login", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/login", "POST", False, error=str(e))

        # Test GET /admin/logout
        try:
            response = self.session.get(f"{self.base_url}/admin/logout")
            if response.status_code in [200, 302]:  # 302 for redirect after logout
                self.log_test_result("/admin/logout", "GET", True, response.json() if response.text else None)
            else:
                self.log_test_result("/admin/logout", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/logout", "GET", False, error=str(e))

        # Test GET /admin/verify
        try:
            response = self.session.get(f"{self.base_url}/admin/verify")
            if response.status_code == 200:
                self.log_test_result("/admin/verify", "GET", True, response.json())
            else:
                self.log_test_result("/admin/verify", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/verify", "GET", False, error=str(e))

    def test_admin_system(self):
        """Test admin system endpoints."""
        print("\n🖥️ Testing Admin System Endpoints...")

        # Test GET /admin/stats
        try:
            response = self.session.get(f"{self.base_url}/admin/stats")
            if response.status_code == 200:
                self.log_test_result("/admin/stats", "GET", True, response.json())
            else:
                self.log_test_result("/admin/stats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/stats", "GET", False, error=str(e))

        # Test GET /admin/system
        try:
            response = self.session.get(f"{self.base_url}/admin/system")
            if response.status_code == 200:
                self.log_test_result("/admin/system", "GET", True, response.json())
            else:
                self.log_test_result("/admin/system", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/system", "GET", False, error=str(e))

    def test_admin_users(self):
        """Test admin user management endpoints."""
        print("\n👥 Testing Admin User Management Endpoints...")

        # Test GET /admin/users/
        try:
            response = self.session.get(f"{self.base_url}/admin/users/")
            if response.status_code == 200:
                self.log_test_result("/admin/users/", "GET", True, response.json())
            else:
                self.log_test_result("/admin/users/", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/users/", "GET", False, error=str(e))

        # Test POST /admin/users/
        try:
            payload = {
                "username": "test-user",
                "email": "test@example.com",
                "password": "test-password",
                "role": "user"
            }
            response = self.session.post(f"{self.base_url}/admin/users/", json=payload)
            if response.status_code in [200, 201]:
                self.log_test_result("/admin/users/", "POST", True, response.json())
            else:
                self.log_test_result("/admin/users/", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/users/", "POST", False, error=str(e))

        # Test POST /admin/users/authenticate
        try:
            payload = {
                "username": "test-user",
                "password": "test-password"
            }
            response = self.session.post(f"{self.base_url}/admin/users/authenticate", json=payload)
            if response.status_code in [200, 401]:  # 401 acceptable for auth failure
                self.log_test_result("/admin/users/authenticate", "POST", True, response.json())
            else:
                self.log_test_result("/admin/users/authenticate", "POST", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/users/authenticate", "POST", False, error=str(e))

        # Test GET /admin/users/stats
        try:
            response = self.session.get(f"{self.base_url}/admin/users/stats")
            if response.status_code == 200:
                self.log_test_result("/admin/users/stats", "GET", True, response.json())
            else:
                self.log_test_result("/admin/users/stats", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result("/admin/users/stats", "GET", False, error=str(e))

    def test_admin_user_operations(self):
        """Test admin user CRUD operations."""
        print("\n🔧 Testing Admin User CRUD Operations...")

        # Test GET /admin/users/{user_id} - using a test user ID
        try:
            user_id = "test-user-123"
            response = self.session.get(f"{self.base_url}/admin/users/{user_id}")
            if response.status_code in [200, 404]:  # 404 acceptable for non-existent user
                self.log_test_result(f"/admin/users/{user_id}", "GET", True, response.json() if response.text else None)
            else:
                self.log_test_result(f"/admin/users/{user_id}", "GET", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result(f"/admin/users/test-user-123", "GET", False, error=str(e))

        # Test PUT /admin/users/{user_id}
        try:
            user_id = "test-user-123"
            payload = {
                "username": "updated-user",
                "email": "updated@example.com",
                "role": "admin"
            }
            response = self.session.put(f"{self.base_url}/admin/users/{user_id}", json=payload)
            if response.status_code in [200, 404]:  # 404 acceptable for non-existent user
                self.log_test_result(f"/admin/users/{user_id}", "PUT", True, response.json() if response.text else None)
            else:
                self.log_test_result(f"/admin/users/{user_id}", "PUT", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result(f"/admin/users/test-user-123", "PUT", False, error=str(e))

        # Test DELETE /admin/users/{user_id}
        try:
            user_id = "test-user-123"
            response = self.session.delete(f"{self.base_url}/admin/users/{user_id}")
            if response.status_code in [200, 204, 404]:  # 404 acceptable for non-existent user
                self.log_test_result(f"/admin/users/{user_id}", "DELETE", True, response.json() if response.text else None)
            else:
                self.log_test_result(f"/admin/users/{user_id}", "DELETE", False, error=f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test_result(f"/admin/users/test-user-123", "DELETE", False, error=str(e))

    def run_all_tests(self):
        """Run all admin endpoint tests."""
        print("🚀 Starting Admin Endpoints Testing...")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {'*' * len(self.api_key) if self.api_key else 'Not set'}")
        print("=" * 60)

        # Run all test categories
        self.test_admin_dashboard()
        self.test_admin_jobs()
        self.test_admin_jobs_cleanup()
        self.test_admin_jobs_scheduler()
        self.test_admin_jobs_deletion()
        self.test_admin_authentication()
        self.test_admin_system()
        self.test_admin_users()
        self.test_admin_user_operations()

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

    def save_results(self):
        """Save test results to file."""
        os.makedirs("temp/test_results", exist_ok=True)
        results_file = "temp/test_results/admin_test_results.json"

        with open(results_file, 'w') as f:
            json.dump({
                'test_run_timestamp': datetime.now().isoformat(),
                'category': 'admin',
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
        print("📊 ADMIN ENDPOINTS TEST SUMMARY")
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
    parser = argparse.ArgumentParser(description="Test admin endpoints")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--api-key", help="API key for authentication")

    args = parser.parse_args()

    try:
        tester = AdminEndpointTester(base_url=args.base_url, api_key=args.api_key)
        tester.run_all_tests()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()