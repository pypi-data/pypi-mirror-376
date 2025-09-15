"""
Hertz07 Python SDK

This is the main entry point for the Hertz07 Python SDK.
"""

from .version import __version__
from .prompt_injection import detect, PromptInjectionDetectionResult

__all__ = [
    "__version__",
    "detect", 
    "PromptInjectionDetectionResult"
]
