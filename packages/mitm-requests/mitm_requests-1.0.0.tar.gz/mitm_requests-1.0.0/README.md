# MITM Proxy Module

A Python module that provides a simple interface for intercepting HTTP/HTTPS requests using mitmproxy, with the ability to capture request/response data and generate curl commands.

## Features

- Easy-to-use Python interface for mitmproxy
- Context manager support for automatic cleanup
- Thread-safe request capture storage
- Parallel request support
- Full curl command generation
- URL-based capture retrieval
- Configurable proxy settings
- Comprehensive error handling and logging

## Installation

This project uses an existing venv with mitmproxy pre-installed:

```bash
# Activate the existing venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install additional required packages
pip install requests
```

## Quick Start

```python
from mitm_requests import MITMProxy
import requests

# Basic usage with context manager
with MITMProxy() as proxy:
    proxies = {'http': proxy.get_proxy_url(), 'https': proxy.get_proxy_url()}
    requests.get('https://httpbin.org/get', proxies=proxies, verify=False)
    
    capture = proxy.get('https://httpbin.org/get')
    if capture:
        print(f"Response: {capture.body}")
        print(f"Curl: {capture.curl}")
```

## API Reference

### MITMProxy Class

- `__init__(port=8080, host='127.0.0.1')`: Initialize proxy
- `start()`: Start the proxy server
- `stop()`: Stop the proxy server  
- `get_proxy_url()`: Get proxy URL for requests
- `get(url)`: Get capture data for specific URL
- `get_all_captures()`: Get all captured data
- `clear_captures()`: Clear all captures
- `is_running()`: Check if proxy is running

### CaptureData Class

- `url`: Request URL
- `method`: HTTP method
- `status_code`: Response status code
- `request_body`: Request body content
- `response_body` / `body`: Response body content
- `curl`: Generated curl command
- `request_headers` / `response_headers`: HTTP headers

## Running Tests

```bash
# Run unit tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_proxy.py -v

# Run with coverage
python -m pytest tests/ --cov=src/mitm_proxy
```

## Examples

### Capturing a Single Request

This example demonstrates how to capture data for a specific URL using the MITMProxy with SeleniumBase.

```python
import requests
import time
from src.mitm_requests import MITMProxy

print("\n=== Example: Capturing a Single Request ===")
with MITMProxy() as proxy:
    print(f"Proxy running on: {proxy.get_proxy_url()}")
    
    finra_url = "https://www.finra.org/finra-data/fixed-income/bond?cusip=912810TZ1&bondType=TS"
    finra_bond_url = "https://services-dynarep.ddwa.finra.org/public/reporting/v2/data/group/FixedIncomeMarket/name/TreasuryEndOfDayPriceYield"    

    from seleniumbase import SB

    with SB(proxy=proxy.get_proxy_url(), chromium_arg="--ignore-certificate-errors", headless=False, uc=True) as sb:
        sb.open(finra_url)
        sb.sleep(3)

    # Get captured data for specific URL
    time.sleep(0.5)  # Allow time for capture
    capture = proxy.get(finra_bond_url)
    if capture:
        print(f"\n=== Captured Data ===")
        print(f"URL: {capture.url}")
        print(f"Method: {capture.method}")
        print(f"Status: {capture.status_code}")
        print(f"Response Body (first 200 chars): {capture.body[:200]}...")
        print(f"\nCurl Command:\n{capture.curl}")
        print(f"\nRaw Response:\n{capture.raw_response.decode('utf-8', errors='replace')}")
    else:
        print("No capture found for the URL")
```

### Capturing All Requests

This example shows how to capture and display data for all intercepted requests.

```python
import requests
import time
from src.mitm_requests import MITMProxy

print("\n=== Example: Capturing All Requests ===")
with MITMProxy() as proxy:
    print(f"Proxy running on: {proxy.get_proxy_url()}")
    
    finra_url = "https://www.finra.org/finra-data/fixed-income/bond?cusip=912810TZ1&bondType=TS"
    finra_bond_url = "https://services-dynarep.ddwa.finra.org/public/reporting/v2/data/group/FixedIncomeMarket/name/TreasuryEndOfDayPriceYield"    

    from seleniumbase import SB

    with SB(proxy=proxy.get_proxy_url(), chromium_arg="--ignore-certificate-errors", headless=False, uc=True) as sb:
        sb.open(finra_url)
        sb.sleep(3)

    # Get all captured data
    time.sleep(0.5)  # Allow time for captures
    captures = proxy.get_all_captures()
    print(f"Captured {len(captures)} requests")
    for capture in captures:
        print(f"\n=== Captured Data ===")
        print(f"URL: {capture.url}")
        print(f"Method: {capture.method}")
        print(f"Status: {capture.status_code}")
        print(f"Response Body (first 200 chars): {capture.body[:200]}...")
        print(f"\nCurl Command:\n{capture.curl}")
        print(f"\nRaw Response:\n{capture.raw_response.decode('utf-8', errors='replace')}")
```

## License

MIT License