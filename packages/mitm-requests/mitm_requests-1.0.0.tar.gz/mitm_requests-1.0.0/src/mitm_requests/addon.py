# src/mitm_proxy/addon.py
import threading
from typing import Dict, Optional, List
from mitmproxy import http
from mitmproxy.addons import export
from .capture import CaptureData

class CaptureAddon:
    """Mitmproxy addon for capturing HTTP flows."""
    
    def __init__(self):
        self.captures: Dict[str, CaptureData] = {}
        self.lock = threading.Lock()
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Called when a request is received."""
        url = flow.request.pretty_url
        
        # Extract request body
        request_body = None
        if flow.request.content:
            try:
                request_body = flow.request.content.decode('utf-8')
            except UnicodeDecodeError:
                request_body = f"<binary data: {len(flow.request.content)} bytes>"
        
        # Create capture data
        capture = CaptureData(
            url=url,
            method=flow.request.method,
            request_headers=dict(flow.request.headers),
            request_body=request_body
        )
        
        # Add raw request
        try:
            capture.raw_request = export.raw_request(flow)
        except Exception as e:
            capture.raw_request = f"Error generating raw request: {str(e)}".encode('utf-8')
        
        with self.lock:
            self.captures[url] = capture
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Called when a response is received."""
        url = flow.request.pretty_url
        
        with self.lock:
            if url in self.captures:
                capture = self.captures[url]
                
                # Update with response data
                capture.status_code = flow.response.status_code
                capture.response_headers = dict(flow.response.headers)
                
                # Extract response body
                if flow.response.content:
                    try:
                        capture.response_body = flow.response.content.decode('utf-8')
                    except UnicodeDecodeError:
                        capture.response_body = f"<binary data: {len(flow.response.content)} bytes>"
                
                # Generate curl command
                try:
                    capture.curl = export.curl_command(flow)
                except Exception as e:
                    capture.curl = f"Error generating curl: {str(e)}"
                
                # Add raw response
                try:
                    capture.raw_response = export.raw_response(flow)
                except Exception as e:
                    capture.raw_response = f"Error generating raw response: {str(e)}".encode('utf-8')
    
    def get_capture(self, url: str) -> Optional[CaptureData]:
        """Get capture data for a specific URL."""
        with self.lock:
            return self.captures.get(url)
    
    def get_all_captures(self) -> List[CaptureData]:
        """Get all capture data."""
        with self.lock:
            return list(self.captures.values())
    
    def clear_captures(self) -> None:
        """Clear all captured data."""
        with self.lock:
            self.captures.clear()