"""
Trasor.io Python SDK Exceptions

Custom exception classes for the Trasor.io SDK.
"""


class TrasorError(Exception):
    """Base exception for all Trasor.io SDK errors"""
    pass


class AuthenticationError(TrasorError):
    """Raised when API key is invalid or unauthorized"""
    pass


class ValidationError(TrasorError):
    """Raised when request parameters are invalid"""
    pass


class APIError(TrasorError):
    """Raised when the API returns an error response"""
    pass