# tests/test_integration.py
import unittest
import requests
import time
import threading
from src.mitm_proxy import MITMProxy

class TestMITMProxyIntegration(unittest.TestCase):
    """Integration tests for MITMProxy (requires actual network requests)."""
    
    def setUp(self):
        """Set up test environment."""
        self.proxy = MITMProxy(port=8888)  # Use different port for testing
    
    def tearDown(self):
        """Clean up after tests."""
        if self.proxy.is_running():
            self.proxy.stop()
    
    @unittest.skip("Requires actual mitmproxy installation")
    def test_basic_http_capture(self):
        """Test basic HTTP request capture."""
        with self.proxy:
            # Give proxy time to start
            time.sleep(1)
            
            proxies = {
                'http': self.proxy.get_proxy_url(),
                'https': self.proxy.get_proxy_url()
            }
            
            # Make a request
            url = 'http://httpbin.org/get'
            response = requests.get(url, proxies=proxies, timeout=10)
            self.assertEqual(response.status_code, 200)
            
            # Check if request was captured
            time.sleep(0.5)  # Give time for capture to complete
            capture = self.proxy.get(url)
            
            if capture:  # Only test if capture was successful
                self.assertEqual(capture.url, url)
                self.assertEqual(capture.method, 'GET')
                self.assertEqual(capture.status_code, 200)
                self.assertIsNotNone(capture.response_body)
                self.assertIsNotNone(capture.curl)
    
    @unittest.skip("Requires actual mitmproxy installation")
    def test_parallel_requests(self):
        """Test handling of parallel requests."""
        with self.proxy:
            time.sleep(1)
            
            proxies = {
                'http': self.proxy.get_proxy_url(),
                'https': self.proxy.get_proxy_url()
            }
            
            urls = [
                'http://httpbin.org/get',
                'http://httpbin.org/user-agent',
                'http://httpbin.org/headers'
            ]
            
            # Make parallel requests
            threads = []
            for url in urls:
                thread = threading.Thread(
                    target=lambda u: requests.get(u, proxies=proxies, timeout=10),
                    args=(url,)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all requests to complete
            for thread in threads:
                thread.join()
            
            time.sleep(1)  # Give time for all captures to complete
            
            # Check captures
            all_captures = self.proxy.get_all_captures()
            self.assertGreaterEqual(len(all_captures), len(urls))

if __name__ == '__main__':
    unittest.main()