"""
Hertz07 Prompt Injection Detection Module

This module provides functionality to detect and analyze potential prompt injection attacks.
"""

from .detector import detect, PromptInjectionDetectionResult

__all__ = [
    "detect",
    "PromptInjectionDetectionResult"
]
