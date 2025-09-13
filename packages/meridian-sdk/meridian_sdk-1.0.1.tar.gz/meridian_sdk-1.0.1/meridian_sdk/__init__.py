"""
Meridian SDK - Python Client Library for Meridian AI Search API

A comprehensive SDK for integrating with the Meridian External API, providing
enterprise search capabilities across connected data sources including SharePoint,
Google Drive, and more.

Basic Usage:
    >>> from meridian_sdk import MeridianAPI
    >>> 
    >>> async with MeridianAPI(api_key="your_key") as client:
    >>>     response = await client.search("Q4 sales numbers")
    >>>     print(response.data)

Features:
    - AI-powered search across enterprise data sources
    - Automatic retry logic with exponential backoff
    - Rate limiting and usage tracking
    - Connector management for data sources
    - Comprehensive error handling
    - Type hints and async/await support
"""

__version__ = "1.0.1"
__author__ = "Meridian Team"
__email__ = "support@meridian.ai"
__license__ = "MIT"

from .client import (
    MeridianAPI,
    MeridianAPIError,
    APIResponse,
    create_client,
    print_response,
)

__all__ = [
    "MeridianAPI",
    "MeridianAPIError", 
    "APIResponse",
    "create_client",
    "print_response",
    "__version__",
]