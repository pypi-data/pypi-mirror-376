# src/mitm_proxy/__init__.py
from .proxy import MITMProxy
from .capture import CaptureData

__all__ = ['MITMProxy', 'CaptureData']
__version__ = '1.0.0'