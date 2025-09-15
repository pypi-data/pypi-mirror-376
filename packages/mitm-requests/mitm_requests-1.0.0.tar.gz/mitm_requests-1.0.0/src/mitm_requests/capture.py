# src/mitm_proxy/capture.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

@dataclass
class CaptureData:
    """Data class to hold captured request/response information."""
    url: str
    method: str
    status_code: Optional[int] = None
    request_headers: Dict[str, str] = None
    response_headers: Dict[str, str] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    curl: Optional[str] = None
    raw_request: Optional[bytes] = None
    raw_response: Optional[bytes] = None
    
    def __post_init__(self):
        if self.request_headers is None:
            self.request_headers = {}
        if self.response_headers is None:
            self.response_headers = {}
    
    @property
    def body(self) -> Optional[str]:
        """Alias for response_body for backward compatibility."""
        return self.response_body
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capture data to dictionary."""
        return {
            'url': self.url,
            'method': self.method,
            'status_code': self.status_code,
            'request_headers': self.request_headers,
            'response_headers': self.response_headers,
            'request_body': self.request_body,
            'response_body': self.response_body,
            'curl': self.curl,
            'raw_request': self.raw_request.decode('utf-8', errors='replace') if self.raw_request else None,
            'raw_response': self.raw_response.decode('utf-8', errors='replace') if self.raw_response else None
        }
    
    def to_json(self) -> str:
        """Convert capture data to JSON string."""
        return json.dumps(self.to_dict(), indent=2)