"""
pytrends-modern: Modern Google Trends API
"""

__version__ = "0.2.3"
__author__ = "pytrends-modern contributors"
__license__ = "MIT"

from pytrends_modern.request import TrendReq
from pytrends_modern.request_async import AsyncTrendReq
from pytrends_modern.rss import TrendsRSS
from pytrends_modern.scraper import TrendsScraper
from pytrends_modern.browser_config_camoufox import BrowserConfig
from pytrends_modern import camoufox_setup
from pytrends_modern.exceptions import (
    TooManyRequestsError,
    ResponseError,
    InvalidParameterError,
    BrowserError,
    DownloadError,
)

__all__ = [
    "TrendReq",
    "AsyncTrendReq",
    "TrendsRSS",
    "TrendsScraper",
    "BrowserConfig",
    "camoufox_setup",
    "TooManyRequestsError",
    "ResponseError",
    "InvalidParameterError",
    "BrowserError",
    "DownloadError",
]
