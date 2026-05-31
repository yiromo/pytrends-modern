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
        self._google_password = None
        
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
        
        import os
        user_data_dir = os.path.expanduser(
            self.browser_config.user_data_dir or "~/.config/camoufox-pytrends-profile"
        )
        
        from pytrends_modern.camoufox_setup import is_profile_configured
        profile_ready = is_profile_configured(user_data_dir)

        google_sign_in_enabled = getattr(self.browser_config, 'google_sign_in', False)
        if not profile_ready and not google_sign_in_enabled:
            raise exceptions.BrowserError(
                f"Camoufox profile not configured at: {user_data_dir}\n"
                "You must set up your Google account login first:\n\n"
                "  from pytrends_modern.camoufox_setup import setup_profile\n"
                "  setup_profile()\n\n"
                "Or run from command line:\n"
                "  python -m pytrends_modern.camoufox_setup\n\n"
                "This will open a browser for you to log in to Google."
            )

        if google_sign_in_enabled:
            from pytrends_modern.camoufox_setup import _resolve_google_password
            self._google_password = _resolve_google_password(
                getattr(self.browser_config, 'google_password', None)
            )
            if not self._google_password:
                raise exceptions.ConfigurationError(
                    "google_sign_in=True but no password provided. "
                    "Set google_password in BrowserConfig or GOOGLE_ACC_PASSWORD env var."
                )
        
        proxy_config = None
        if self.browser_config.proxy_server:
            proxy_config = {
                "server": self.browser_config.proxy_server,
            }
            if self.browser_config.proxy_username:
                proxy_config["username"] = self.browser_config.proxy_username
            if self.browser_config.proxy_password:
                proxy_config["password"] = self.browser_config.proxy_password
        
        firefox_user_prefs = getattr(self.browser_config, 'firefox_user_prefs', None)

        try:
            camoufox_manager = AsyncCamoufox(
                persistent_context=self.browser_config.persistent_context,
                user_data_dir=user_data_dir if self.browser_config.persistent_context else None,
                headless=self.browser_config.headless,
                humanize=self.browser_config.humanize if hasattr(self.browser_config, 'humanize') else True,
                os=self.browser_config.os if hasattr(self.browser_config, 'os') else 'linux',
                geoip=self.browser_config.geoip if hasattr(self.browser_config, 'geoip') else True,
                proxy=proxy_config,
                config=self.browser_config.custom_config if self.browser_config.custom_config else None,
                firefox_user_prefs=firefox_user_prefs if firefox_user_prefs else None,
            )
            
            self.browser = camoufox_manager
            self.browser_context = await camoufox_manager.__aenter__()
            
            if self.browser_context.pages:
                self.browser_page = self.browser_context.pages[0]
            else:
                self.browser_page = await self.browser_context.new_page()
            
            self.browser_page.on("response", self._handle_network_response)

            if not profile_ready and google_sign_in_enabled and self._google_password:
                await self._ensure_signed_in()
            
        except exceptions.BrowserError:
            raise
        except exceptions.ConfigurationError:
            raise
        except Exception as e:
            raise exceptions.BrowserError(f"Failed to initialize AsyncCamoufox: {e}")
    
    async def _close_browser(self) -> None:
        """Close browser if open (async)"""
        if self.browser:
            try:
                await self.browser.__aexit__(None, None, None)
            except Exception:
                pass
            self.browser = None
            self.browser_context = None
            self.browser_page = None
    
    async def _ensure_signed_in(self) -> None:
        """
        Navigate to Google Trends and auto sign-in if needed (async).

        Only runs when google_sign_in=True. If already signed in,
        returns immediately.
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")

        password = getattr(self, '_google_password', None)
        if not password:
            return

        try:
            await self.browser_page.goto(
                "https://trends.google.com/trends/explore?q=Python&legacy&hl=en-GB",
                wait_until='networkidle',
                timeout=60000,
            )
            import asyncio
            await asyncio.sleep(1)

            from pytrends_modern.camoufox_setup import auto_google_sign_in_async
            await auto_google_sign_in_async(self.browser_page, password)
        except exceptions.BrowserError:
            raise
        except Exception as e:
            raise exceptions.BrowserError(f"Auto sign-in failed: {e}")
    
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

            # Remove Google's JSONP prefix
            if body.startswith(b")]}',\n"):
                body = body[6:]
            elif body.startswith(b")]}',"):
                body = body[5:]
            elif body.startswith(b")]}'\n"):
                body = body[5:]
            elif body.startswith(b")]}'"):
                body = body[4:]
            
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
        
        # Get timeframe from config (default: 'today 1-m')
        timeframe = getattr(self.browser_config, 'timeframe', 'today 1-m')
        
        # Get YouTube mode from config (default: False)
        youtube = getattr(self.browser_config, 'youtube', False)
        
        # Build URL with or without date parameter
        if timeframe == 'today 12-m':
            # Past 12 months - no date parameter needed
            base_url = f"https://trends.google.com/trends/explore?q={encoded_keyword}"
        else:
            # Default: today 1-m or custom timeframe
            encoded_timeframe = urllib.parse.quote(timeframe)
            base_url = f"https://trends.google.com/trends/explore?date={encoded_timeframe}&q={encoded_keyword}"
        
        # Add YouTube property if enabled
        if youtube:
            base_url += "&gprop=youtube"
        
        # Add language and legacy parameter
        url = base_url + "&legacy&hl=en-GB"
        
        try:
            await self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
            
            import asyncio
            await asyncio.sleep(2)

            if getattr(self.browser_config, 'google_sign_in', False):
                from pytrends_modern.camoufox_setup import _afind_sign_in_button
                password = getattr(self, '_google_password', None)
                if await _afind_sign_in_button(self.browser_page) and password:
                    await self._ensure_signed_in()
                    await asyncio.sleep(1)
                    self.browser_responses_cache.clear()
                    await self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
                    await asyncio.sleep(2)
            
        except Exception as e:
            if "Auto sign-in failed" in str(e):
                raise exceptions.BrowserError(str(e))
            raise exceptions.BrowserError(f"Failed to navigate to Google Trends: {e}")

    async def _capture_analysis_responses(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> None:
        """
        Navigate to the Explore page without a query and capture trending
        analysis responses (related topics + queries) via network interception (async).

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m')
            geo: Country code (e.g. 'RU', 'KZ') or empty for worldwide
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('', 'youtube', 'news', etc.)
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")

        await self._add_request_delay()
        self.browser_responses_cache.clear()

        import urllib.parse
        encoded_timeframe = urllib.parse.quote(timeframe)
        url = f"https://trends.google.com/trends/explore?date={encoded_timeframe}"
        if geo:
            url += f"&geo={geo}"
        if gprop:
            url += f"&gprop={gprop}"
        url += f"&hl={hl}"

        try:
            await self.browser_page.goto(url, wait_until='networkidle', timeout=60000)

            import asyncio
            await asyncio.sleep(3)

            if getattr(self.browser_config, 'google_sign_in', False):
                from pytrends_modern.camoufox_setup import _afind_sign_in_button
                password = getattr(self, '_google_password', None)
                if await _afind_sign_in_button(self.browser_page) and password:
                    await self._ensure_signed_in()
                    await asyncio.sleep(1)
                    self.browser_responses_cache.clear()
                    await self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
                    await asyncio.sleep(3)

        except Exception as e:
            if "Auto sign-in failed" in str(e):
                raise exceptions.BrowserError(str(e))
            raise exceptions.BrowserError(f"Failed to navigate to Google Trends analysis: {e}")

    async def _scrape_interest_over_time_from_svg(self) -> pd.DataFrame:
        """
        Scrape interest over time data from the SVG chart (async).

        Fallback when the API network responses are empty (429/500 from Google).
        """
        import re
        from datetime import datetime, timedelta

        try:
            page = self.browser_page

            chart_svg = page.locator('svg[aria-label]')
            if await chart_svg.count() == 0:
                raise exceptions.ResponseError("No SVG chart found on page")

            path_elem = chart_svg.locator('path').first
            d_attr = await path_elem.get_attribute('d')
            if not d_attr:
                raise exceptions.ResponseError("SVG path has no d attribute")

            coords = [float(v) for v in re.findall(r'[\d.]+', d_attr)]
            if len(coords) < 4:
                raise exceptions.ResponseError("Too few coordinates in SVG path")
            points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]

            clip_rect = chart_svg.locator('clipPath rect').first
            x_left = float(await clip_rect.get_attribute('x') or '30')
            y_top = float(await clip_rect.get_attribute('y') or '17')
            width = float(await clip_rect.get_attribute('width') or '839')
            height = float(await clip_rect.get_attribute('height') or '186')
            y_bottom = y_top + height
            x_right = x_left + width

            text_elements = await chart_svg.locator('text').all()
            text_values = []
            for t in text_elements:
                val = await t.text_content()
                if val:
                    text_values.append(val.strip().replace('\u202a', '').replace('\u202c', ''))

            x_dates = []
            for val in text_values:
                for fmt in ('%b %d, %Y', '%B %d, %Y', '%Y-%m-%d', '%I:%M %p'):
                    try:
                        x_dates.append(datetime.strptime(val, fmt))
                        break
                    except ValueError:
                        continue

            if len(x_dates) < 2:
                timeframe = getattr(self.browser_config, 'timeframe', 'today 1-m')
                now = datetime.now()
                from pytrends_modern.request import TrendReq
                x_dates = TrendReq._timeframe_to_dates(timeframe, now)

            if len(x_dates) >= 2:
                date_start = x_dates[0]
                date_end = x_dates[-1]
            else:
                date_start = datetime.now() - timedelta(days=30)
                date_end = datetime.now()

            total_span = (date_end - date_start).total_seconds()
            keyword = self.kw_list[0] if self.kw_list else 'keyword'

            rows = []
            for x, y in points:
                value = max(0, min(100, round((y_bottom - y) / height * 100)))
                if total_span > 0:
                    frac = (x - x_left) / (x_right - x_left)
                    dt = date_start + timedelta(seconds=frac * total_span)
                else:
                    dt = date_start
                rows.append({
                    'date': dt,
                    keyword: value,
                    'isPartial': False,
                })

            df = pd.DataFrame(rows)
            df = df.set_index('date').sort_index()
            return df

        except exceptions.ResponseError:
            raise
        except Exception as e:
            raise exceptions.ResponseError(f"Failed to scrape SVG chart: {e}")
    
    def _parse_multiline_response(self, data: Dict) -> pd.DataFrame:
        """Parse multiline (interest over time) API response"""
        from pytrends_modern.request import TrendReq
        return TrendReq._parse_multiline_response(self, data)
    
    def _parse_comparedgeo_response(self, data: Dict, inc_geo_code: bool = False) -> pd.DataFrame:
        """Parse comparedgeo (interest by region) API response"""
        from pytrends_modern.request import TrendReq
        return TrendReq._parse_comparedgeo_response(self, data, inc_geo_code)
    
    def _parse_relatedsearches_response(self, data: Dict) -> Dict[str, Optional[pd.DataFrame]]:
        """Parse relatedsearches (related topics/queries) API response"""
        from pytrends_modern.request import TrendReq
        return TrendReq._parse_relatedsearches_response(self, data)
    
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
            return await self._scrape_interest_over_time_from_svg()
        
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

    async def trending_analysis_topics(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get trending analysis topics (async) — Explore page without query keyword.

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m')
            geo: Country code (e.g. 'RU', 'KZ', 'US'). Empty = worldwide.
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('' for web, 'youtube', 'news', etc.)

        Returns:
            Dictionary with 'top' and 'rising' DataFrames of trending topics.
        """
        if not self.browser_responses_cache.get('related_topics'):
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)

        response_data = self.browser_responses_cache.get('related_topics')

        if not response_data:
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)
            response_data = self.browser_responses_cache.get('related_topics')

        if not response_data:
            raise exceptions.ResponseError(
                "Failed to capture trending analysis topics response"
            )

        return self._parse_relatedsearches_response(response_data)

    async def trending_analysis_queries(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get trending analysis queries (async) — Explore page without query keyword.

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m')
            geo: Country code (e.g. 'RU', 'KZ', 'US'). Empty = worldwide.
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('' for web, 'youtube', 'news', etc.)

        Returns:
            Dictionary with 'top' and 'rising' DataFrames of trending queries.
        """
        if not self.browser_responses_cache.get('related_queries'):
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)

        response_data = self.browser_responses_cache.get('related_queries')

        if not response_data:
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)
            response_data = self.browser_responses_cache.get('related_queries')

        if not response_data:
            raise exceptions.ResponseError(
                "Failed to capture trending analysis queries response"
            )

        return self._parse_relatedsearches_response(response_data)

    async def trending_analysis_merged(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> Dict[str, Dict[str, Optional[pd.DataFrame]]]:
        """
        Get both trending topics and queries in a single browser navigation (async).

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m')
            geo: Country code (e.g. 'RU', 'KZ', 'US'). Empty = worldwide.
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('' for web, 'youtube', 'news', etc.)

        Returns:
            Dictionary with 'topics' and 'queries' keys, each containing
            {'top': DataFrame, 'rising': DataFrame}.
        """
        has_topics = bool(self.browser_responses_cache.get('related_topics'))
        has_queries = bool(self.browser_responses_cache.get('related_queries'))

        if not has_topics or not has_queries:
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)

        topics_data = self.browser_responses_cache.get('related_topics')
        queries_data = self.browser_responses_cache.get('related_queries')

        if not topics_data or not queries_data:
            await self._capture_analysis_responses(timeframe, geo, hl, gprop)
            topics_data = self.browser_responses_cache.get('related_topics')
            queries_data = self.browser_responses_cache.get('related_queries')

        result = {}
        if topics_data:
            result['topics'] = self._parse_relatedsearches_response(topics_data)
        else:
            result['topics'] = {"top": None, "rising": None}

        if queries_data:
            result['queries'] = self._parse_relatedsearches_response(queries_data)
        else:
            result['queries'] = {"top": None, "rising": None}

        return result
