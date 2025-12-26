"""
pytrends-modern: Modern Google Trends API
"""

__version__ = "1.0.0"
__author__ = "pytrends-modern contributors"
__license__ = "MIT"

from pytrends_modern.request import TrendReq
from pytrends_modern.rss import TrendsRSS
from pytrends_modern.scraper import TrendsScraper
from pytrends_modern.exceptions import (
    TooManyRequestsError,
    ResponseError,
    InvalidParameterError,
    BrowserError,
    DownloadError,
)

__all__ = [
    "TrendReq",
    "TrendsRSS",
    "TrendsScraper",
    "TooManyRequestsError",
    "ResponseError",
    "InvalidParameterError",
    "BrowserError",
    "DownloadError",
]
