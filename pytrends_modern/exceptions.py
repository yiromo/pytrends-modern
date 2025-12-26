"""
Exceptions for pytrends-modern
"""

from typing import Optional
from requests import Response


class PyTrendsPlusError(Exception):
    """Base exception for pytrends-modern"""

    pass


class ResponseError(PyTrendsPlusError):
    """Exception for HTTP response errors"""

    def __init__(self, message: str, response: Optional[Response] = None):
        super().__init__(message)
        self.response = response

    @classmethod
    def from_response(cls, response: Response) -> "ResponseError":
        """Create ResponseError from requests.Response object"""
        message = (
            f"The request failed: Google returned status code {response.status_code}. "
            f"URL: {response.url}"
        )
        if response.text:
            message += f"\nResponse: {response.text[:200]}"
        return cls(message, response)


class TooManyRequestsError(ResponseError):
    """Exception for rate limiting (HTTP 429)"""

    @classmethod
    def from_response(cls, response: Response) -> "TooManyRequestsError":
        """Create TooManyRequestsError from requests.Response object"""
        message = (
            "You have reached your quota limit. Google is rate limiting your requests. "
            "Please try again later or use proxies."
        )
        return cls(message, response)


class InvalidParameterError(PyTrendsPlusError):
    """Exception for invalid parameters"""

    pass


class BrowserError(PyTrendsPlusError):
    """Exception for Selenium browser errors"""

    pass


class DownloadError(PyTrendsPlusError):
    """Exception for download errors"""

    pass


class ConfigurationError(PyTrendsPlusError):
    """Exception for configuration errors"""

    pass
