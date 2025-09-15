# tests/test_proxy.py
import unittest
import time
import requests
from unittest.mock import patch, MagicMock
from src.mitm_proxy import MITMProxy, CaptureData

class TestMITMProxy(unittest.TestCase):
    """Test cases for MITMProxy class."""
    
    def test_proxy_initialization(self):
        """Test proxy initialization with custom parameters."""
        proxy = MITMProxy(port=9090, host='localhost')
        self.assertEqual(proxy.port, 9090)
        self.assertEqual(proxy.host, 'localhost')
        self.assertFalse(proxy.is_running())
    
    def test_get_proxy_url(self):
        """Test proxy URL generation."""
        proxy = MITMProxy(port=8080, host='127.0.0.1')
        self.assertEqual(proxy.get_proxy_url(), 'http://127.0.0.1:8080')
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with patch.object(MITMProxy, 'start') as mock_start, \
             patch.object(MITMProxy, 'stop') as mock_stop:
            
            with MITMProxy() as proxy:
                self.assertIsInstance(proxy, MITMProxy)
            
            mock_start.assert_called_once()
            mock_stop.assert_called_once()

class TestCaptureData(unittest.TestCase):
    """Test cases for CaptureData class."""
    
    def test_capture_data_creation(self):
        """Test CaptureData creation and properties."""
        capture = CaptureData(
            url='https://example.com',
            method='GET',
            status_code=200,
            response_body='test response'
        )
        
        self.assertEqual(capture.url, 'https://example.com')
        self.assertEqual(capture.method, 'GET')
        self.assertEqual(capture.status_code, 200)
        self.assertEqual(capture.body, 'test response')  # Test alias
        self.assertEqual(capture.response_body, 'test response')
    
    def test_capture_data_to_dict(self):
        """Test conversion to dictionary."""
        capture = CaptureData(
            url='https://example.com',
            method='POST',
            request_body='{"test": "data"}',
            raw_request=b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n',
            raw_response=b'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'
        )
        
        data_dict = capture.to_dict()
        self.assertEqual(data_dict['url'], 'https://example.com')
        self.assertEqual(data_dict['method'], 'POST')
        self.assertEqual(data_dict['request_body'], '{"test": "data"}')
        self.assertEqual(data_dict['raw_request'], 'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
        self.assertEqual(data_dict['raw_response'], 'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n')

if __name__ == '__main__':
    unittest.main()