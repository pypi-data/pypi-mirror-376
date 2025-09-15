# src/mitm_proxy/proxy.py
import asyncio
import threading
import time
from typing import Optional
import logging
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from .addon import CaptureAddon
from .capture import CaptureData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MITMProxy:
    """
    A wrapper around mitmproxy for easy HTTP/HTTPS traffic capture.
    
    Usage:
        # With context manager (recommended)
        with MITMProxy() as proxy:
            # Make requests using proxy.get_proxy_url()
            capture = proxy.get('https://example.com')
        
        # Manual control
        proxy = MITMProxy()
        proxy.start()
        # ... make requests ...
        proxy.stop()
    """
    
    def __init__(self, port: int = 8080, host: str = '127.0.0.1'):
        """
        Initialize MITM proxy.
        
        Args:
            port: Port to run the proxy on
            host: Host to bind the proxy to
        """
        self.port = port
        self.host = host
        self.master: Optional[DumpMaster] = None
        self.addon = CaptureAddon()
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._started = threading.Event()
        
    def _run_proxy(self):
        """Run the proxy in a separate thread."""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Configure mitmproxy options
            opts = Options(
                listen_host=self.host,
                listen_port=self.port,
                confdir="~/.mitmproxy",
            )
            
            # Create and configure master - pass the loop explicitly
            self.master = DumpMaster(opts, loop=self.loop)
            self.master.addons.add(self.addon)
            
            # Signal that proxy is starting
            self._running = True
            self._started.set()
            
            logger.info(f"Starting MITM proxy on {self.host}:{self.port}")
            
            # Run the proxy
            self.loop.run_until_complete(self.master.run())
            
        except Exception as e:
            logger.error(f"Error running proxy: {e}")
            self._running = False
            self._started.set()  # Signal even on error
    
    def start(self) -> None:
        """Start the proxy server."""
        if self._running:
            logger.warning("Proxy is already running")
            return
        
        # Start proxy in separate thread
        self.thread = threading.Thread(target=self._run_proxy, daemon=True)
        self.thread.start()
        
        # Wait for proxy to start (with timeout)
        if not self._started.wait(timeout=10):
            raise RuntimeError("Proxy failed to start within 10 seconds")
        
        if not self._running:
            raise RuntimeError("Proxy failed to start")
        
        # Give proxy a moment to fully initialize
        time.sleep(0.5)
        logger.info(f"MITM proxy started successfully on {self.host}:{self.port}")
    
    def stop(self) -> None:
        """Stop the proxy server."""
        if not self._running:
            return
        
        logger.info("Stopping MITM proxy...")
        self._running = False
        
        if self.master and self.loop:
            # Schedule shutdown in the proxy's event loop
            def shutdown():
                if self.master:
                    # shutdown() might not be a coroutine, handle both cases
                    try:
                        shutdown_coro = self.master.shutdown()
                        if shutdown_coro is not None:
                            asyncio.create_task(shutdown_coro)
                    except Exception as e:
                        logger.warning(f"Error during shutdown: {e}")
            
            try:
                self.loop.call_soon_threadsafe(shutdown)
            except Exception as e:
                logger.warning(f"Error scheduling shutdown: {e}")
        
        # Wait for thread to finish (with timeout)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("MITM proxy stopped")
    
    def get_proxy_url(self) -> str:
        """Get the proxy URL for use with requests."""
        return f"http://{self.host}:{self.port}"
    
    def get(self, url: str) -> Optional[CaptureData]:
        """
        Get captured data for a specific URL.
        
        Args:
            url: The URL to get capture data for
            
        Returns:
            CaptureData object if found, None otherwise
        """
        return self.addon.get_capture(url)
    
    def get_all_captures(self) -> dict:
        """Get all captured data."""
        return self.addon.get_all_captures()
    
    def clear_captures(self) -> None:
        """Clear all captured data."""
        self.addon.clear_captures()
    
    def is_running(self) -> bool:
        """Check if the proxy is running."""
        return self._running
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()