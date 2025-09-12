"""
shrutiAI - A Python SDK for interacting with shrutiAI API
"""

from .client import ShrutiAIClient
from .exceptions import ShrutiAIError, AuthenticationError, RateLimitError

__version__ = "1.0.0"
__all__ = ["ShrutiAIClient", "ShrutiAIError", "AuthenticationError", "RateLimitError"]
