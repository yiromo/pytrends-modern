"""
Async Google Trends API request module with Camoufox support
"""

import json
from typing import Dict, Optional
from urllib.parse import quote

import pandas as pd

from pytrends_modern import exceptions
from pytrends_modern.browser_config_camoufox import BrowserConfig


class AsyncTrendReq:
    """
    Async Google Trends API with Camoufox browser mode support
    
    This class provides async methods for fetching Google Trends data
    using Camoufox's async API for better performance in async applications.
    
    Example:
        >>> import asyncio
        >>> from pytrends_modern import AsyncTrendReq, BrowserConfig
        >>> 
        >>> async def main():
        ...     config = BrowserConfig(headless=True)
        ...     async with AsyncTrendReq(browser_config=config) as pytrends:
        ...         pytrends.kw_list = ['Python']
        ...         df = await pytrends.interest_over_time()
        ...         print(df.head())
        >>> 
        >>> asyncio.run(main())
    """
    
    def __init__(self, browser_config: BrowserConfig):
        """
        Initialize async Google Trends request
        
        Args:
            browser_config: BrowserConfig instance for Camoufox
        """
        self.browser_config = browser_config
        self.browser = None
        self.browser_context = None
        self.browser_page = None
        self.browser_responses_cache = {}
        self.kw_list = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._init_camoufox()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_browser()
        
    def _browserforge_to_camoufox(self, fingerprint) -> Dict:
        """Convert BrowserForge fingerprint to Camoufox config"""
        # Reuse the sync version's implementation
        from pytrends_modern.request import TrendReq
        return TrendReq._browserforge_to_camoufox(self, fingerprint)
    
    async def _add_request_delay(self) -> None:
        """Add random delay between requests to avoid rate limiting (async)"""
        if hasattr(self.browser_config, 'min_delay') and hasattr(self.browser_config, 'max_delay'):
            import asyncio
            import random
            delay = random.uniform(self.browser_config.min_delay, self.browser_config.max_delay)
            await asyncio.sleep(delay)
    
    async def _init_camoufox(self) -> None:
        """Initialize Camoufox browser with persistent context (async)"""
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            raise ImportError(
                "Camoufox is required for async browser mode. "
                "Install with: pip install pytrends-modern[browser]"
            )
        
        # Prepare browser options
        import os
        user_data_dir = os.path.expanduser(
            self.browser_config.user_data_dir or "~/.config/camoufox-pytrends-profile"
        )
        
        # Check if profile is configured (has Google login)
        from pytrends_modern.camoufox_setup import is_profile_configured
        if not is_profile_configured(user_data_dir):
            raise exceptions.BrowserError(
                f"Camoufox profile not configured at: {user_data_dir}\n"
                "You must set up your Google account login first:\n\n"
                "  from pytrends_modern.camoufox_setup import setup_profile\n"
                "  setup_profile()\n\n"
                "Or run from command line:\n"
                "  python -m pytrends_modern.camoufox_setup\n\n"
                "This will open a browser for you to log in to Google."
            )
        
        # Proxy configuration (if provided)
        proxy_config = None
        if self.browser_config.proxy_server:
            proxy_config = {
                "server": self.browser_config.proxy_server,
            }
            if self.browser_config.proxy_username:
                proxy_config["username"] = self.browser_config.proxy_username
            if self.browser_config.proxy_password:
                proxy_config["password"] = self.browser_config.proxy_password
        
        # Initialize AsyncCamoufox with persistent context
        try:
            # Note: Camoufox automatically generates BrowserForge fingerprints
            # based on the 'os' parameter. No need to manually pass fingerprints.
            
            # AsyncCamoufox() returns a context manager
            camoufox_manager = AsyncCamoufox(
                persistent_context=self.browser_config.persistent_context,
                user_data_dir=user_data_dir if self.browser_config.persistent_context else None,
                headless=self.browser_config.headless,
                humanize=self.browser_config.humanize if hasattr(self.browser_config, 'humanize') else True,
                os=self.browser_config.os if hasattr(self.browser_config, 'os') else 'linux',
                geoip=self.browser_config.geoip if hasattr(self.browser_config, 'geoip') else True,
                proxy=proxy_config,
                config=self.browser_config.custom_config if self.browser_config.custom_config else None
            )
            
            # Enter the context manager to get the browser context
            self.browser = camoufox_manager
            self.browser_context = await camoufox_manager.__aenter__()
            
            # Use existing page if available (avoid opening 2 tabs)
            if self.browser_context.pages:
                self.browser_page = self.browser_context.pages[0]
            else:
                self.browser_page = await self.browser_context.new_page()
            
            # Set up network interception
            self.browser_page.on("response", self._handle_network_response)
            
        except Exception as e:
            raise exceptions.BrowserError(f"Failed to initialize AsyncCamoufox: {e}")
    
    async def _close_browser(self) -> None:
        """Close browser if open (async)"""
        if self.browser:
            try:
                # Exit the context manager
                await self.browser.__aexit__(None, None, None)
            except Exception:
                pass
            self.browser = None
            self.browser_context = None
            self.browser_page = None
    
    async def _handle_network_response(self, response) -> None:
        """
        Handle network responses and cache Google Trends API data (async)
        
        Args:
            response: Playwright response object
        """
        url = response.url
        
        # Only process Google Trends API responses
        if '/trends/api/widgetdata/' not in url:
            return
        
        try:
            # Get response body (async in AsyncPlaywright)
            body = await response.body()
            
            # Parse the response (remove Google's JSONP prefix - exactly 5 bytes)
            if body.startswith(b")]}'\n"):
                body = body[5:]
            elif body.startswith(b")]}'"):
                body = body[5:]
            
            data = json.loads(body)
            
            # Cache by URL pattern
            if '/widgetdata/multiline' in url:
                self.browser_responses_cache['interest_over_time'] = data
            elif '/widgetdata/comparedgeo' in url:
                self.browser_responses_cache['interest_by_region'] = data
            elif '/widgetdata/relatedsearches' in url:
                # keywordType is URL-encoded inside the req parameter
                import urllib.parse
                decoded_url = urllib.parse.unquote(url)
                if 'keywordType":"ENTITY' in decoded_url:
                    self.browser_responses_cache['related_topics'] = data
                elif 'keywordType":"QUERY' in decoded_url:
                    self.browser_responses_cache['related_queries'] = data
                    
        except Exception:
            pass  # Silently ignore parsing errors
    
    async def _capture_all_api_responses(self, keyword: str) -> None:
        """
        Navigate once and capture ALL API responses via network interception (async)
        
        Args:
            keyword: Search keyword to use
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")
        
        # Add random delay before request (anti-rate-limiting)
        await self._add_request_delay()
        
        # Clear cache
        self.browser_responses_cache.clear()
        
        # Build URL
        import urllib.parse
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://trends.google.com/trends/explore?date=today%201-m&q={encoded_keyword}&hl=en-GB"
        
        try:
            # Navigate and wait for network idle
            await self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Give extra time for any delayed API calls
            import asyncio
            await asyncio.sleep(2)
            
        except Exception as e:
            raise exceptions.BrowserError(f"Failed to navigate to Google Trends: {e}")
    
    def _parse_multiline_response(self, data: Dict) -> pd.DataFrame:
        """Parse multiline (interest over time) API response"""
        # Import from sync version to reuse parsing logic
        from pytrends_modern.request import TrendReq
        temp = TrendReq(hl='en-US', tz=360)
        return temp._parse_multiline_response(data)
    
    def _parse_comparedgeo_response(self, data: Dict, inc_geo_code: bool = False) -> pd.DataFrame:
        """Parse comparedgeo (interest by region) API response"""
        from pytrends_modern.request import TrendReq
        temp = TrendReq(hl='en-US', tz=360)
        return temp._parse_comparedgeo_response(data, inc_geo_code)
    
    def _parse_relatedsearches_response(self, data: Dict) -> Dict[str, Optional[pd.DataFrame]]:
        """Parse relatedsearches (related topics/queries) API response"""
        from pytrends_modern.request import TrendReq
        temp = TrendReq(hl='en-US', tz=360)
        return temp._parse_relatedsearches_response(data)
    
    async def interest_over_time(self) -> pd.DataFrame:
        """
        Get interest over time data (async)
        
        Returns:
            DataFrame with date index and columns for each keyword
        """
        if len(self.kw_list) != 1:
            raise exceptions.InvalidParameterError(
                "Async browser mode only supports 1 keyword. You provided: "
                + str(len(self.kw_list))
            )
        
        keyword = self.kw_list[0]
        
        # Capture all responses if not already cached
        if not self.browser_responses_cache:
            await self._capture_all_api_responses(keyword)
        
        # Get cached response
        response_data = self.browser_responses_cache.get('interest_over_time')
        
        if not response_data:
            # Try one more navigation if cache is empty
            await self._capture_all_api_responses(keyword)
            response_data = self.browser_responses_cache.get('interest_over_time')
            
        if not response_data:
            raise exceptions.ResponseError("Failed to capture interest_over_time API response")
        
        # Parse browser response to DataFrame
        return self._parse_multiline_response(response_data)
    
    async def interest_by_region(self, inc_geo_code: bool = False) -> pd.DataFrame:
        """
        Get interest by region data (async)
        
        Args:
            inc_geo_code: Include geographic codes in results
            
        Returns:
            DataFrame with region index
        """
        if len(self.kw_list) != 1:
            raise exceptions.InvalidParameterError(
                "Async browser mode only supports 1 keyword"
            )
        
        keyword = self.kw_list[0]
        
        # Capture all responses if not already cached
        if not self.browser_responses_cache:
            await self._capture_all_api_responses(keyword)
        
        # Get cached response
        response_data = self.browser_responses_cache.get('interest_by_region')
        
        if not response_data:
            raise exceptions.ResponseError("Failed to capture interest_by_region API response")
        
        return self._parse_comparedgeo_response(response_data, inc_geo_code)
    
    async def related_topics(self) -> Dict[str, Dict[str, Optional[pd.DataFrame]]]:
        """
        Get related topics (async)
        
        Returns:
            Dict with keyword as key and dict of 'top'/'rising' DataFrames as value
        """
        if len(self.kw_list) != 1:
            raise exceptions.InvalidParameterError(
                "Async browser mode only supports 1 keyword"
            )
        
        keyword = self.kw_list[0]
        
        # Capture all responses if not already cached
        if not self.browser_responses_cache:
            await self._capture_all_api_responses(keyword)
        
        # Get cached response
        response_data = self.browser_responses_cache.get('related_topics')
        
        if not response_data:
            raise exceptions.ResponseError("Failed to capture related_topics API response")
        
        return {keyword: self._parse_relatedsearches_response(response_data)}
    
    async def related_queries(self) -> Dict[str, Dict[str, Optional[pd.DataFrame]]]:
        """
        Get related queries (async)
        
        Returns:
            Dict with keyword as key and dict of 'top'/'rising' DataFrames as value
        """
        if len(self.kw_list) != 1:
            raise exceptions.InvalidParameterError(
                "Async browser mode only supports 1 keyword"
            )
        
        keyword = self.kw_list[0]
        
        # Capture all responses if not already cached
        if not self.browser_responses_cache:
            await self._capture_all_api_responses(keyword)
        
        # Get cached response
        response_data = self.browser_responses_cache.get('related_queries')
        
        if not response_data:
            raise exceptions.ResponseError("Failed to capture related_queries API response")
        
        return {keyword: self._parse_relatedsearches_response(response_data)}
