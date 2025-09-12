"""
Trasor.io Python SDK

A developer-friendly Python SDK for integrating with Trasor.io's trust infrastructure platform.
Provides secure, immutable audit trails for AI agent workflows.
"""

from .client import TrasorClient
from .exceptions import TrasorError, AuthenticationError, ValidationError, APIError

__version__ = "2.0.0"
__author__ = "Trasor.io"
__email__ = "support@trasor.io"
__license__ = "MIT"

__all__ = [
    "TrasorClient",
    "TrasorError",
    "AuthenticationError", 
    "ValidationError",
    "APIError",
]