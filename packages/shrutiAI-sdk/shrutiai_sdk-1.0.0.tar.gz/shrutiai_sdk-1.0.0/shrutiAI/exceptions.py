"""
Custom exceptions for shrutiAI SDK
"""


class ShrutiAIError(Exception):
    """Base exception for all API-related errors"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(ShrutiAIError):
    """Raised when API key is invalid or missing"""
    pass


class RateLimitError(ShrutiAIError):
    """Raised when API rate limit is exceeded"""
    pass


class NotFoundError(ShrutiAIError):
    """Raised when requested resource is not found"""
    pass


class ValidationError(ShrutiAIError):
    """Raised when request data is invalid"""
    pass
