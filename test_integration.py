#!/usr/bin/env python3
"""
Integration test for the unified Driver AI Co-Pilot application
Tests both frontend serving and API functionality
"""
import requests
import time
import sys
import subprocess
import threading
from pathlib import Path

class UnifiedAppTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.server_process = None
        
    def start_server(self):
        """Start the Flask server in background"""
        try:
            backend_dir = Path("backend")
            self.server_process = subprocess.Popen(
                ["python", "run.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Give server time to start
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and "frontend" in data:
                    print("✅ Health endpoint working")
                    return True
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def test_frontend_serving(self):
        """Test that frontend is being served"""
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                content = response.text
                if "Driver AI Co-Pilot" in content or "<!DOCTYPE html>" in content:
                    print("✅ Frontend serving working")
                    return True
            print(f"❌ Frontend serving failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Frontend serving error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints are accessible"""
        try:
            # Test signup endpoint (should return error without data, but endpoint should exist)
            response = requests.post(f"{self.base_url}/api/auth/signup", json={}, timeout=5)
            if response.status_code in [400, 422]:  # Expected error for empty data
                print("✅ API endpoints accessible")
                return True
            print(f"❌ API endpoints failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ API endpoints error: {e}")
            return False
    
    def test_static_assets(self):
        """Test that static assets are served"""
        try:
            # Try to access assets directory
            response = requests.get(f"{self.base_url}/assets/", timeout=5)
            # Assets directory might return 404, but server should respond
            if response.status_code in [200, 404, 403]:
                print("✅ Static assets routing working")
                return True
            print(f"❌ Static assets failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Static assets error: {e}")
            return False
    
    def run_tests(self):
        """Run all integration tests"""
        print("🧪 Running Unified Application Integration Tests")
        print("=" * 50)
        
        # Check if frontend is built
        dist_path = Path("frontend/dist")
        if not dist_path.exists():
            print("❌ Frontend not built. Run 'npm run build' first.")
            return False
        
        print("✅ Frontend build found")
        
        # Start server
        print("🚀 Starting server...")
        if not self.start_server():
            return False
        
        try:
            # Wait for server to be ready
            print("⏳ Waiting for server to be ready...")
            time.sleep(2)
            
            # Run tests
            tests = [
                self.test_health_endpoint,
                self.test_frontend_serving,
                self.test_api_endpoints,
                self.test_static_assets
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if test():
                    passed += 1
                time.sleep(0.5)
            
            print("\n" + "=" * 50)
            print(f"📊 Test Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed! Unified application is working correctly.")
                print(f"🌐 Access your application at: {self.base_url}")
                return True
            else:
                print("❌ Some tests failed. Check the output above.")
                return False
                
        finally:
            print("🛑 Stopping server...")
            self.stop_server()

def main():
    """Main test runner"""
    tester = UnifiedAppTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()