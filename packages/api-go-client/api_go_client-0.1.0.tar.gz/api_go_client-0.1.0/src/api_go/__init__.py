"""
API Framework - Простой фреймворк для работы с API
"""

from api_go.src.api_go.client import APIClient
from .exceptions import APIException, HTTPError, AuthenticationError, RateLimitError
from .decorators import retry, rate_limit
from .utils import APIUtils

__version__ = '1.0.0'
__all__ = [
    'APIClient',
    'APIException',
    'HTTPError',
    'AuthenticationError',
    'RateLimitError',
    'retry',
    'rate_limit',
    'APIUtils'
]