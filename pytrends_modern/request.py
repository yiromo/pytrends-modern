"""
Main Google Trends API request module
"""

import json
import random
import time
from itertools import product
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import quote

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from pytrends_modern import exceptions
from pytrends_modern.browser_config_camoufox import BrowserConfig
from pytrends_modern.config import (
    BASE_TRENDS_URL,
    CATEGORIES_URL,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_GEO,
    DEFAULT_HL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    DEFAULT_TZ,
    ERROR_CODES,
    GENERAL_URL,
    INTEREST_BY_REGION_URL,
    INTEREST_OVER_TIME_URL,
    MULTIRANGE_INTEREST_OVER_TIME_URL,
    REALTIME_TRENDING_SEARCHES_URL,
    RELATED_QUERIES_URL,
    SUGGESTIONS_URL,
    TODAY_SEARCHES_URL,
    TOP_CHARTS_URL,
    TRENDING_SEARCHES_URL,
    USER_AGENTS,
    VALID_GPROP,
)


class TrendReq:
    """
    Google Trends API - Enhanced version

    Features:
    - Full pytrends compatibility
    - Enhanced error handling with automatic retries
    - Proxy rotation support
    - User agent rotation
    - Better rate limit handling
    - Type hints throughout

    Example:
        >>> pytrends = TrendReq(hl='en-US', tz=360)
        >>> pytrends.build_payload(['Python', 'JavaScript'], timeframe='today 12-m')
        >>> df = pytrends.interest_over_time()
    """

    GET_METHOD = "get"
    POST_METHOD = "post"

    def __init__(
        self,
        hl: str = DEFAULT_HL,
        tz: int = DEFAULT_TZ,
        geo: str = DEFAULT_GEO,
        timeout: Tuple[int, int] = DEFAULT_TIMEOUT,
        proxies: Optional[Union[List[str], Dict[str, str]]] = None,
        retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        requests_args: Optional[Dict[str, Any]] = None,
        rotate_user_agent: bool = True,
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Initialize Google Trends API client

        Args:
            hl: Language code (e.g., 'en-US', 'es-ES')
            tz: Timezone offset in minutes (e.g., 360 for US CST)
            geo: Geographic location (e.g., 'US', 'GB', 'US-CA')
            timeout: (connect_timeout, read_timeout) in seconds
            proxies: List of proxy URLs or dict of proxies {'http': '...', 'https': '...'}
            retries: Number of retry attempts
            backoff_factor: Backoff factor for exponential backoff
            requests_args: Additional arguments to pass to requests
            rotate_user_agent: Whether to rotate user agents
            browser_config: DrissionPage browser configuration (experimental)
                           
                           ⚠️ LIMITATIONS when using browser_config:
                           - Only 1 keyword supported (no comparison)
                           - Only WORLDWIDE geo supported (no geo filtering)
                           - Requires Chrome/Chromium browser installed
        """
        # Browser mode initialization
        self.browser_config = browser_config
        self.browser = None
        self.browser_context = None
        self.browser_page = None
        self.browser_mode = browser_config is not None
        self.browser_responses_cache = {}  # Cache for captured API responses
        
        if self.browser_mode:
            import warnings
            warnings.warn(
                "⚠️  Camoufox browser mode is EXPERIMENTAL and has limitations:\n"
                "   - Only 1 keyword supported (no keyword comparison)\n"
                "   - Timeframe: 'today 1-m' (default) or 'today 12-m'\n"
                "   - Only WORLDWIDE geo supported\n"
                "   - Requires Google account login (first run)\n"
                "   - Login session is saved for future runs",
                UserWarning,
                stacklevel=2
            )
            self._init_camoufox()
        
        # Rate limit message from Google
        self.google_rl = "You have reached your quota limit. Please try again later."

        # Initialize instance variables
        self.results: Optional[Dict] = None
        self.tz = tz
        self.hl = hl
        self.geo = geo
        self.kw_list: List[str] = []
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.rotate_user_agent = rotate_user_agent
        self.requests_args = requests_args or {}

        # Handle proxies
        self.proxies: List[str] = []
        self.proxy_index = 0
        if proxies:
            if isinstance(proxies, list):
                self.proxies = proxies
            elif isinstance(proxies, dict):
                # Store dict format in requests_args
                self.requests_args["proxies"] = proxies

        # Get initial cookies (skip in browser mode)
        if not self.browser_mode:
            self.cookies = self._get_google_cookie()
        else:
            self.cookies = {}

        # Initialize widget payloads
        self.token_payload: Dict[str, Any] = {}
        self.interest_over_time_widget: Dict[str, Any] = {}
        self.interest_by_region_widget: Dict[str, Any] = {}
        self.related_topics_widget_list: List[Dict[str, Any]] = []
        self.related_queries_widget_list: List[Dict[str, Any]] = []

        # Setup headers
        self.headers = {"accept-language": self.hl}
        if self.rotate_user_agent:
            self.headers["User-Agent"] = random.choice(USER_AGENTS)
        self.headers.update(self.requests_args.pop("headers", {}))
    
    def __del__(self):
        """Cleanup browser on object deletion"""
        self._close_browser()

    def _get_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(USER_AGENTS) if self.rotate_user_agent else USER_AGENTS[0]
    
    def _browserforge_to_camoufox(self, fingerprint) -> Dict:
        """Convert BrowserForge fingerprint to Camoufox config"""
        config = {}
        
        # Navigator properties
        if hasattr(fingerprint, 'navigator'):
            nav = fingerprint.navigator
            if hasattr(nav, 'userAgent'):
                config['navigator.userAgent'] = nav.userAgent
            if hasattr(nav, 'language'):
                config['navigator.language'] = nav.language
            if hasattr(nav, 'hardwareConcurrency'):
                config['navigator.hardwareConcurrency'] = nav.hardwareConcurrency
            if hasattr(nav, 'maxTouchPoints'):
                config['navigator.maxTouchPoints'] = nav.maxTouchPoints
        
        # Screen properties
        if hasattr(fingerprint, 'screen'):
            scr = fingerprint.screen
            if hasattr(scr, 'width'):
                config['screen.width'] = scr.width
            if hasattr(scr, 'height'):
                config['screen.height'] = scr.height
            if hasattr(scr, 'availWidth'):
                config['screen.availWidth'] = scr.availWidth
            if hasattr(scr, 'availHeight'):
                config['screen.availHeight'] = scr.availHeight
        
        return config
    
    def _add_request_delay(self) -> None:
        """Add random delay between requests to avoid rate limiting"""
        if hasattr(self.browser_config, 'min_delay') and hasattr(self.browser_config, 'max_delay'):
            import time
            import random
            delay = random.uniform(self.browser_config.min_delay, self.browser_config.max_delay)
            time.sleep(delay)
    
    def _init_camoufox(self) -> None:
        """Initialize Camoufox browser with persistent context"""
        try:
            from camoufox.sync_api import Camoufox
        except ImportError:
            raise ImportError(
                "Camoufox is required for browser mode. "
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
        else:
            self._google_password = None
        
        proxy_config = None
        if self.browser_config.proxy_server:
            proxy_config = {
                "server": self.browser_config.proxy_server,
            }
            if self.browser_config.proxy_username:
                proxy_config["username"] = self.browser_config.proxy_username
            if self.browser_config.proxy_password:
                proxy_config["password"] = self.browser_config.proxy_password
        
        try:
            camoufox_manager = Camoufox(
                persistent_context=self.browser_config.persistent_context,
                user_data_dir=user_data_dir if self.browser_config.persistent_context else None,
                headless=self.browser_config.headless,
                humanize=self.browser_config.humanize if hasattr(self.browser_config, 'humanize') else True,
                os=self.browser_config.os if hasattr(self.browser_config, 'os') else 'linux',
                geoip=self.browser_config.geoip if hasattr(self.browser_config, 'geoip') else True,
                proxy=proxy_config,
                config=self.browser_config.custom_config if self.browser_config.custom_config else None
            )
            
            self.browser = camoufox_manager
            self.browser_context = camoufox_manager.__enter__()
            
            if self.browser_context.pages:
                self.browser_page = self.browser_context.pages[0]
            else:
                self.browser_page = self.browser_context.new_page()
            
            self.browser_page.on("response", self._handle_network_response)

            if not profile_ready and google_sign_in_enabled and self._google_password:
                self._ensure_signed_in()
            
        except exceptions.BrowserError:
            raise
        except exceptions.ConfigurationError:
            raise
        except Exception as e:
            raise exceptions.BrowserError(f"Failed to initialize Camoufox: {e}")
    
    def _close_browser(self) -> None:
        """Close browser if open"""
        if self.browser:
            try:
                self.browser.__exit__(None, None, None)
            except Exception:
                pass
            self.browser = None
            self.browser_context = None
            self.browser_page = None
    
    def _ensure_signed_in(self) -> None:
        """
        Navigate to Google Trends and auto sign-in if needed.

        Only runs when google_sign_in=True. Navigates to Google Trends,
        checks for 'Sign in' button, and performs automated login if found.
        If already signed in, returns immediately.
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")

        password = getattr(self, '_google_password', None)
        if not password:
            return

        try:
            self.browser_page.goto(
                "https://trends.google.com/trends/explore?q=Python&legacy&hl=en-GB",
                wait_until='networkidle',
                timeout=60000,
            )
            import time
            time.sleep(1)

            from pytrends_modern.camoufox_setup import auto_google_sign_in
            auto_google_sign_in(self.browser_page, password)
        except Exception as e:
            raise exceptions.BrowserError(f"Auto sign-in failed: {e}")
    
    def _handle_network_response(self, response) -> None:
        """
        Handle network responses and cache Google Trends API data
        
        Args:
            response: Playwright response object
        """
        url = response.url
        
        # Only process Google Trends API responses
        if '/trends/api/widgetdata/' not in url:
            return
        
        try:
            # Get response body
            body = response.body()
            
# Parse the response (remove Google's JSONP prefix
            if body.startswith(b")]}'\n"):
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
    
    def _capture_all_api_responses(self, keyword: str) -> None:
        """
        Navigate once and capture ALL API responses via network interception
        
        Args:
            keyword: Search keyword to use
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")
        
        # Add random delay before request (anti-rate-limiting)
        self._add_request_delay()
        
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
            self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
            
            import time
            time.sleep(2)

            if getattr(self.browser_config, 'google_sign_in', False):
                from pytrends_modern.camoufox_setup import _find_sign_in_button
                password = getattr(self, '_google_password', None)
                if _find_sign_in_button(self.browser_page) and password:
                    from pytrends_modern.camoufox_setup import auto_google_sign_in
                    auto_google_sign_in(self.browser_page, password)
                    time.sleep(1)
                    self.browser_responses_cache.clear()
                    self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
                    time.sleep(2)
            
        except Exception as e:
            if "Auto sign-in failed" in str(e):
                raise exceptions.BrowserError(str(e))
            raise exceptions.BrowserError(f"Failed to navigate to Google Trends: {e}")

    def _capture_analysis_responses(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> None:
        """
        Navigate to the Explore page without a query and capture trending
        analysis responses (related topics + queries) via network interception.

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m')
            geo: Country code (e.g. 'RU', 'KZ') or empty for worldwide
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('', 'youtube', 'news', etc.)
        """
        if not self.browser_page:
            raise exceptions.BrowserError("Browser not initialized")

        self._add_request_delay()
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
            self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
            import time
            time.sleep(3)

            if getattr(self.browser_config, 'google_sign_in', False):
                from pytrends_modern.camoufox_setup import _find_sign_in_button
                password = getattr(self, '_google_password', None)
                if _find_sign_in_button(self.browser_page) and password:
                    from pytrends_modern.camoufox_setup import auto_google_sign_in
                    auto_google_sign_in(self.browser_page, password)
                    time.sleep(1)
                    self.browser_responses_cache.clear()
                    self.browser_page.goto(url, wait_until='networkidle', timeout=60000)
                    time.sleep(3)

        except Exception as e:
            if "Auto sign-in failed" in str(e):
                raise exceptions.BrowserError(str(e))
            raise exceptions.BrowserError(f"Failed to navigate to Google Trends analysis: {e}")

    def _parse_api_response(self, response_text: str) -> Dict:
        """
        Parse API response from Google Trends
        
        Google's API responses may contain garbage prefix: ")]}',\n"
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed JSON data
        """
        # Remove garbage prefix if present
        if response_text.startswith(")]}',\n"):
            response_text = response_text[6:]
        elif response_text.startswith(")]}',"):
            response_text = response_text[5:]
        elif response_text.startswith(")]},"):
            response_text = response_text[5:]
        elif response_text.startswith(")]}'"):
            response_text = response_text[4:]
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise exceptions.ResponseError(f"Failed to parse API response: {e}")
    
    def _scrape_interest_over_time_from_svg(self) -> pd.DataFrame:
        """
        Scrape interest over time data from the SVG chart rendered in the browser.

        Fallback when the API network responses are empty (429/500 from Google).
        Parses the SVG <path d="M..."> coordinates and maps them to dates/values
        using chart bounds and axis labels.

        Returns:
            DataFrame with date index, keyword column, and isPartial column.

        Raises:
            exceptions.ResponseError: If SVG chart cannot be found or parsed.
        """
        import re
        from datetime import datetime, timedelta

        try:
            page = self.browser_page

            chart_svg = page.locator('svg[aria-label]')
            if chart_svg.count() == 0:
                raise exceptions.ResponseError("No SVG chart found on page")

            path_elem = chart_svg.locator('path').first
            d_attr = path_elem.get_attribute('d')
            if not d_attr:
                raise exceptions.ResponseError("SVG path has no d attribute")

            coords = [float(v) for v in re.findall(r'[\d.]+', d_attr)]
            if len(coords) < 4:
                raise exceptions.ResponseError("Too few coordinates in SVG path")
            points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]

            clip_rect = chart_svg.locator('clipPath rect').first
            x_left = float(clip_rect.get_attribute('x') or '30')
            y_top = float(clip_rect.get_attribute('y') or '17')
            width = float(clip_rect.get_attribute('width') or '839')
            height = float(clip_rect.get_attribute('height') or '186')
            y_bottom = y_top + height
            x_right = x_left + width

            text_elements = chart_svg.locator('text').all()
            text_values = []
            for t in text_elements:
                val = t.text_content()
                if val:
                    text_values.append(val.strip().replace('\u202a', '').replace('\u202c', ''))

            x_dates = []
            for val in text_values:
                try:
                    dt = datetime.strptime(val, '%b %d, %Y')
                    x_dates.append(dt)
                    continue
                except ValueError:
                    pass
                try:
                    dt = datetime.strptime(val, '%B %d, %Y')
                    x_dates.append(dt)
                    continue
                except ValueError:
                    pass
                try:
                    dt = datetime.strptime(val, '%Y-%m-%d')
                    x_dates.append(dt)
                    continue
                except ValueError:
                    pass
                try:
                    dt = datetime.strptime(val, '%I:%M %p')
                    x_dates.append(dt)
                    continue
                except ValueError:
                    pass

            if len(x_dates) < 2:
                timeframe = getattr(self.browser_config, 'timeframe', 'today 1-m')
                now = datetime.now()
                x_dates = self._timeframe_to_dates(timeframe, now)

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

    @staticmethod
    def _timeframe_to_dates(timeframe: str, now) -> list:
        """Convert a Google Trends timeframe string to [start, end] datetime list."""
        from datetime import timedelta

        mapping = {
            'now 1-H': timedelta(hours=1),
            'now 4-H': timedelta(hours=4),
            'now 1-d': timedelta(days=1),
            'now 7-d': timedelta(days=7),
            'today 1-m': timedelta(days=30),
            'today 3-m': timedelta(days=90),
            'today 12-m': timedelta(days=365),
            'today 5-y': timedelta(days=365 * 5),
        }
        delta = mapping.get(timeframe, timedelta(days=30))
        return [now - delta, now]

    def _parse_multiline_response(self, data: Dict) -> pd.DataFrame:
        """
        Parse multiline API response (interest over time)
        
        Args:
            data: Parsed JSON response from multiline API
            
        Returns:
            DataFrame with date index and keyword columns
        """
        try:
            timeline_data = data.get('default', {}).get('timelineData', [])
            
            if not timeline_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(timeline_data)
            
            # Convert timestamps to datetime
            df["date"] = pd.to_datetime(df["time"].astype("float64"), unit="s")
            df = df.set_index("date").sort_index()
            
            # Parse values
            result_df = df["value"].apply(
                lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
            )
            
            # Name columns with keywords
            for idx, kw in enumerate(self.kw_list):
                result_df.insert(len(result_df.columns), kw, result_df[idx].astype("int"))
                del result_df[idx]
            
            # Add isPartial column
            if "isPartial" in df:
                df["isPartial"] = df["isPartial"].where(df["isPartial"].notna(), False)
                is_partial_df = df["isPartial"].apply(
                    lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
                )
                is_partial_df.columns = ["isPartial"]
                is_partial_df["isPartial"] = is_partial_df["isPartial"] == "True"
                final_df = pd.concat([result_df, is_partial_df], axis=1)
            else:
                final_df = result_df
                final_df["isPartial"] = False
            
            return final_df
            
        except Exception as e:
            raise exceptions.ResponseError(f"Failed to parse multiline response: {e}")
    
    def _parse_comparedgeo_response(self, data: Dict, inc_geo_code: bool = False) -> pd.DataFrame:
        """
        Parse comparedgeo API response (interest by region)
        
        Args:
            data: Parsed JSON response from comparedgeo API
            inc_geo_code: Include geographic codes in output
            
        Returns:
            DataFrame with geographic distribution
        """
        try:
            geo_data = data.get('default', {}).get('geoMapData', [])
            
            if not geo_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(geo_data)
            
            # Determine geo column name
            geo_column = "geoCode" if "geoCode" in df.columns else "coordinates"
            columns = ["geoName", geo_column, "value"]
            df = df[columns].set_index("geoName").sort_index()
            
            # Parse values
            result_df = df["value"].apply(
                lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
            )
            
            # Name columns with keywords
            for idx, kw in enumerate(self.kw_list):
                result_df.insert(len(result_df.columns), kw, result_df[idx].astype("int"))
                del result_df[idx]
            
            # Add geo code if requested
            if inc_geo_code and geo_column in df.columns:
                result_df[geo_column] = df[geo_column]
            
            return result_df
            
        except Exception as e:
            raise exceptions.ResponseError(f"Failed to parse comparedgeo response: {e}")
    
    def _parse_relatedsearches_response(self, data: Dict) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Parse relatedsearches API response (related queries or topics)
        
        Args:
            data: Parsed JSON response from relatedsearches API
            
        Returns:
            Dictionary with 'top' and 'rising' DataFrames
        """
        try:
            ranked_list = data.get('default', {}).get('rankedList', [])
            
            # Parse top
            try:
                top_data = ranked_list[0]['rankedKeyword']
                if 'topic' in str(top_data[0]) if top_data else False:
                    # Topics format
                    df_top = pd.json_normalize(top_data, sep="_")
                else:
                    # Queries format
                    df_top = pd.DataFrame(top_data)
                    df_top = df_top[["query", "value"]] if "query" in df_top.columns else df_top
            except (KeyError, IndexError):
                df_top = None
            
            # Parse rising
            try:
                rising_data = ranked_list[1]['rankedKeyword']
                if 'topic' in str(rising_data[0]) if rising_data else False:
                    # Topics format
                    df_rising = pd.json_normalize(rising_data, sep="_")
                else:
                    # Queries format
                    df_rising = pd.DataFrame(rising_data)
                    df_rising = df_rising[["query", "value"]] if "query" in df_rising.columns else df_rising
            except (KeyError, IndexError):
                df_rising = None
            
            return {"top": df_top, "rising": df_rising}
            
        except Exception as e:
            raise exceptions.ResponseError(f"Failed to parse relatedsearches response: {e}")

    def _get_google_cookie(self) -> Dict[str, str]:
        """
        Get Google NID cookie for requests

        Returns:
            Dictionary containing NID cookie

        Raises:
            exceptions.ResponseError: If unable to get cookie
        """
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            try:
                # Build request kwargs
                kwargs = dict(self.requests_args)

                # Handle proxies
                if self.proxies and len(self.proxies) > 0:
                    proxy = {"https": self.proxies[self.proxy_index]}
                    kwargs["proxies"] = proxy

                # Make request
                response = requests.get(
                    f"{BASE_TRENDS_URL}/?geo={self.hl[-2:]}",
                    timeout=self.timeout,
                    headers={"User-Agent": self._get_user_agent()},
                    **kwargs,
                )

                # Extract NID cookie
                cookies = dict(filter(lambda i: i[0] == "NID", response.cookies.items()))
                if cookies:
                    return cookies

            except requests.exceptions.ProxyError:
                print(f"[WARN] Proxy error with proxy {self.proxy_index}. Trying next...")
                if len(self.proxies) > 1:
                    self.proxies.pop(self.proxy_index)
                    if self.proxy_index >= len(self.proxies):
                        self.proxy_index = 0
                else:
                    raise exceptions.ResponseError("No working proxies available")

            except Exception as e:
                print(f"[WARN] Error getting cookie (attempt {attempt + 1}/{max_attempts}): {e}")

            attempt += 1
            if attempt < max_attempts:
                time.sleep(1 * attempt)  # Exponential backoff

        # Return empty dict if all attempts fail (some endpoints work without cookies)
        print("[WARN] Could not get Google cookie, proceeding without it")
        return {}

    def _get_new_proxy(self) -> None:
        """Rotate to next proxy in list"""
        if len(self.proxies) > 0:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)

    def _get_data(
        self, url: str, method: str = GET_METHOD, trim_chars: int = 0, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send request to Google Trends and return JSON response

        Args:
            url: Target URL
            method: HTTP method ('get' or 'post')
            trim_chars: Number of characters to trim from response start
            **kwargs: Additional arguments for request

        Returns:
            Parsed JSON response as dictionary

        Raises:
            exceptions.TooManyRequestsError: If rate limited (HTTP 429)
            exceptions.ResponseError: For other HTTP errors
        """
        # Create session
        session = requests.Session()

        # Setup retries if configured
        if self.retries > 0 or self.backoff_factor > 0:
            retry_strategy = Retry(
                total=self.retries,
                read=self.retries,
                connect=self.retries,
                backoff_factor=self.backoff_factor,
                status_forcelist=ERROR_CODES,
                allowed_methods=frozenset(["GET", "POST"]),
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

        # Update session headers
        session.headers.update(self.headers)

        # Handle proxy rotation
        if self.proxies and len(self.proxies) > 0:
            self.cookies = self._get_google_cookie()
            session.proxies.update({"https": self.proxies[self.proxy_index]})

        # Make request
        try:
            if method == self.POST_METHOD:
                response = session.post(
                    url, timeout=self.timeout, cookies=self.cookies, **kwargs, **self.requests_args
                )
            else:
                response = session.get(
                    url, timeout=self.timeout, cookies=self.cookies, **kwargs, **self.requests_args
                )
        except requests.exceptions.RequestException as e:
            raise exceptions.ResponseError(f"Request failed: {str(e)}")

        # Check response status
        if response.status_code == 429:
            raise exceptions.TooManyRequestsError.from_response(response)

        # Check if response contains JSON
        content_type = response.headers.get("Content-Type", "")
        if response.status_code == 200 and any(
            t in content_type
            for t in ["application/json", "application/javascript", "text/javascript"]
        ):
            # Trim garbage characters and parse JSON
            content = response.text[trim_chars:]
            try:
                data = json.loads(content)
                self._get_new_proxy()  # Rotate proxy on success
                return data
            except json.JSONDecodeError as e:
                raise exceptions.ResponseError(f"Invalid JSON response: {str(e)}")

        # Handle error responses
        raise exceptions.ResponseError.from_response(response)

    def build_payload(
        self,
        kw_list: List[str],
        cat: int = 0,
        timeframe: Union[str, List[str]] = "today 5-y",
        geo: str = "",
        gprop: str = "",
    ) -> None:
        """
        Build payload for Google Trends request

        Args:
            kw_list: List of keywords (max 5)
            cat: Category ID (0 for all categories)
            timeframe: Time range (e.g., 'today 12-m', 'now 7-d')
                      Can be list for multirange queries
            geo: Geographic location (e.g., 'US', 'GB', 'US-CA')
            gprop: Google property ('', 'images', 'news', 'youtube', 'froogle')

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate gprop
        if gprop not in VALID_GPROP:
            raise ValueError(f"gprop must be one of {VALID_GPROP}, got '{gprop}'")

        # Validate keyword count
        if len(kw_list) > 5:
            raise ValueError("Maximum 5 keywords allowed")

        if len(kw_list) == 0:
            raise ValueError("At least one keyword required")

        # Store keywords and geo
        self.kw_list = kw_list
        self.geo = geo or self.geo

        # Build token payload
        self.token_payload = {
            "hl": self.hl,
            "tz": self.tz,
            "req": {"comparisonItem": [], "category": cat, "property": gprop},
        }

        # Handle multiple geos
        geo_list = self.geo if isinstance(self.geo, list) else [self.geo]

        # Build comparison items
        if isinstance(timeframe, list):
            # Multirange: each keyword-geo pair gets its own timeframe
            for index, (kw, g) in enumerate(product(self.kw_list, geo_list)):
                keyword_payload = {"keyword": kw, "time": timeframe[index], "geo": g}
                self.token_payload["req"]["comparisonItem"].append(keyword_payload)
        else:
            # Single timeframe for all keyword-geo pairs
            for kw, g in product(self.kw_list, geo_list):
                keyword_payload = {"keyword": kw, "time": timeframe, "geo": g}
                self.token_payload["req"]["comparisonItem"].append(keyword_payload)

        # Convert req to JSON string (required by Google's API)
        self.token_payload["req"] = json.dumps(self.token_payload["req"])

        # Get tokens from Google (skip in browser mode)
        if not self.browser_mode:
            self._get_tokens()

    def _get_tokens(self) -> None:
        """
        Get API tokens from Google Trends for different widget types

        This method must be called after build_payload() to retrieve
        the necessary tokens for subsequent API calls.
        """
        # Make request to get widget configurations
        widget_dicts = self._get_data(
            url=GENERAL_URL,
            method=self.POST_METHOD,
            params=self.token_payload,
            trim_chars=4,
        )["widgets"]

        # Clear previous widget lists
        self.related_queries_widget_list.clear()
        self.related_topics_widget_list.clear()

        # Parse widgets
        first_region_token = True
        for widget in widget_dicts:
            widget_id = widget.get("id", "")

            if widget_id == "TIMESERIES":
                self.interest_over_time_widget = widget
            elif widget_id == "GEO_MAP" and first_region_token:
                self.interest_by_region_widget = widget
                first_region_token = False
            elif "RELATED_TOPICS" in widget_id:
                self.related_topics_widget_list.append(widget)
            elif "RELATED_QUERIES" in widget_id:
                self.related_queries_widget_list.append(widget)

    def interest_over_time(self) -> pd.DataFrame:
        """
        Get interest over time data

        Returns:
            DataFrame with date index and columns for each keyword.
            Includes 'isPartial' column indicating if latest data is partial.

        Example:
            >>> pytrends.build_payload(['Python'], timeframe='today 12-m')
            >>> df = pytrends.interest_over_time()
            >>> print(df.head())
        """
        # Browser mode: capture multiline API response
        if self.browser_mode:
            if len(self.kw_list) != 1:
                raise exceptions.InvalidParameterError(
                    "Browser mode only supports 1 keyword. You provided: "
                    + str(len(self.kw_list))
                )
            
            keyword = self.kw_list[0]
            
            # Capture all responses if not already cached
            if not self.browser_responses_cache:
                self._capture_all_api_responses(keyword)
            
            # Get cached response
            response_data = self.browser_responses_cache.get('interest_over_time')
            
            if not response_data:
                # Try one more navigation if cache is empty
                self._capture_all_api_responses(keyword)
                response_data = self.browser_responses_cache.get('interest_over_time')
                
            if not response_data:
                return self._scrape_interest_over_time_from_svg()
            
            return self._parse_multiline_response(response_data)
        
        # Standard mode: use widgets
        if not self.interest_over_time_widget:
            raise exceptions.ResponseError(
                "No interest over time widget available. Call build_payload() first."
            )

        # Build request payload
        payload = {
            "req": json.dumps(self.interest_over_time_widget["request"]),
            "token": self.interest_over_time_widget["token"],
            "tz": self.tz,
        }

        # Get data
        req_json = self._get_data(
            url=INTEREST_OVER_TIME_URL,
            method=self.GET_METHOD,
            trim_chars=5,
            params=payload,
        )

        # Parse response
        df = pd.DataFrame(req_json["default"]["timelineData"])

        if df.empty:
            return df

        # Convert timestamps to datetime
        df["date"] = pd.to_datetime(df["time"].astype("float64"), unit="s")
        df = df.set_index("date").sort_index()

        # Parse values
        result_df = df["value"].apply(
            lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
        )

        # Name columns with keywords
        geo_list = self.geo if isinstance(self.geo, list) else [self.geo]
        for idx, (kw, g) in enumerate(product(self.kw_list, geo_list)):
            name = kw if len(geo_list) == 1 else (kw, g)
            result_df.insert(len(result_df.columns), name, result_df[idx].astype("int"))
            del result_df[idx]

        # Add isPartial column
        if "isPartial" in df:
            df["isPartial"] = df["isPartial"].where(df["isPartial"].notna(), False)
            is_partial_df = df["isPartial"].apply(
                lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
            )
            is_partial_df.columns = ["isPartial"]
            is_partial_df["isPartial"] = is_partial_df["isPartial"] == "True"
            final_df = pd.concat([result_df, is_partial_df], axis=1)
        else:
            final_df = result_df
            final_df["isPartial"] = False

        # Handle multi-geo with MultiIndex
        if len(geo_list) > 1:
            final_df.columns = pd.MultiIndex.from_tuples(
                [c if isinstance(c, tuple) else (c,) for c in final_df], names=["keyword", "region"]
            )

        return final_df

    def interest_by_region(
        self,
        resolution: Literal["COUNTRY", "REGION", "CITY", "DMA"] = "COUNTRY",
        inc_low_vol: bool = False,
        inc_geo_code: bool = False,
    ) -> pd.DataFrame:
        """
        Get interest by geographic region

        Args:
            resolution: Geographic resolution level
            inc_low_vol: Include regions with low search volume
            inc_geo_code: Include geographic codes in output

        Returns:
            DataFrame with geographic distribution of search interest

        Example:
            >>> pytrends.build_payload(['Python'], geo='US')
            >>> df = pytrends.interest_by_region(resolution='REGION')
            >>> print(df.head())
        """
        # Browser mode: capture comparedgeo API response
        if self.browser_mode:
            if len(self.kw_list) != 1:
                raise exceptions.InvalidParameterError(
                    "Browser mode only supports 1 keyword"
                )
            
            keyword = self.kw_list[0]
            
            # Capture all responses if not already cached
            if not self.browser_responses_cache:
                self._capture_all_api_responses(keyword)
            
            # Get cached response
            response_data = self.browser_responses_cache.get('interest_by_region')
            
            if not response_data:
                raise exceptions.ResponseError("Failed to capture interest_by_region API response")
            
            return self._parse_comparedgeo_response(response_data, inc_geo_code)
        
        # Standard mode
        if not self.interest_by_region_widget:
            raise exceptions.ResponseError(
                "No interest by region widget available. Call build_payload() first."
            )

        # Set resolution
        if self.geo == "" or (self.geo == "US" and resolution in ["DMA", "CITY", "REGION"]):
            self.interest_by_region_widget["request"]["resolution"] = resolution

        self.interest_by_region_widget["request"]["includeLowSearchVolumeGeos"] = inc_low_vol

        # Build payload
        payload = {
            "req": json.dumps(self.interest_by_region_widget["request"]),
            "token": self.interest_by_region_widget["token"],
            "tz": self.tz,
        }

        # Get data
        req_json = self._get_data(
            url=INTEREST_BY_REGION_URL,
            method=self.GET_METHOD,
            trim_chars=5,
            params=payload,
        )

        # Parse response
        df = pd.DataFrame(req_json["default"]["geoMapData"])

        if df.empty:
            return df

        # Determine geo column name
        geo_column = "geoCode" if "geoCode" in df.columns else "coordinates"
        columns = ["geoName", geo_column, "value"]
        df = df[columns].set_index("geoName").sort_index()

        # Parse values
        result_df = df["value"].apply(
            lambda x: pd.Series(str(x).replace("[", "").replace("]", "").split(","))
        )

        # Add geo code if requested
        if inc_geo_code and geo_column in df.columns:
            result_df[geo_column] = df[geo_column]

        # Name columns with keywords
        for idx, kw in enumerate(self.kw_list):
            result_df[kw] = result_df[idx].astype("int")
            del result_df[idx]

        return result_df

    def related_topics(self) -> Dict[str, Dict[str, Optional[pd.DataFrame]]]:
        """
        Get related topics for each keyword

        Returns:
            Dictionary with keywords as keys, each containing:
                - 'top': DataFrame of top related topics
                - 'rising': DataFrame of rising related topics

        Example:
            >>> pytrends.build_payload(['Python'])
            >>> topics = pytrends.related_topics()
            >>> print(topics['Python']['top'].head())
        """
        # Browser mode: capture relatedsearches ENTITY API response
        if self.browser_mode:
            if len(self.kw_list) != 1:
                raise exceptions.InvalidParameterError(
                    "Browser mode only supports 1 keyword"
                )
            
            keyword = self.kw_list[0]
            
            # Capture all responses if not already cached
            if not self.browser_responses_cache:
                self._capture_all_api_responses(keyword)
            
            # Get cached response
            response_data = self.browser_responses_cache.get('related_topics')
            
            if not response_data:
                raise exceptions.ResponseError("Failed to capture related_topics API response")
            
            return {keyword: self._parse_relatedsearches_response(response_data)}
        
        # Standard mode
        if not self.related_topics_widget_list:
            raise exceptions.ResponseError(
                "No related topics widgets available. Call build_payload() first."
            )

        result_dict = {}

        for widget in self.related_topics_widget_list:
            # Extract keyword
            try:
                kw = widget["request"]["restriction"]["complexKeywordsRestriction"]["keyword"][0][
                    "value"
                ]
            except (KeyError, IndexError):
                kw = ""

            # Build payload
            payload = {
                "req": json.dumps(widget["request"]),
                "token": widget["token"],
                "tz": self.tz,
            }

            # Get data
            req_json = self._get_data(
                url=RELATED_QUERIES_URL,
                method=self.GET_METHOD,
                trim_chars=5,
                params=payload,
            )

            # Parse top topics
            try:
                top_list = req_json["default"]["rankedList"][0]["rankedKeyword"]
                df_top = pd.json_normalize(top_list, sep="_")
            except (KeyError, IndexError):
                df_top = None

            # Parse rising topics
            try:
                rising_list = req_json["default"]["rankedList"][1]["rankedKeyword"]
                df_rising = pd.json_normalize(rising_list, sep="_")
            except (KeyError, IndexError):
                df_rising = None

            result_dict[kw] = {"top": df_top, "rising": df_rising}

        return result_dict

    def related_queries(self) -> Dict[str, Dict[str, Optional[pd.DataFrame]]]:
        """
        Get related search queries for each keyword

        Returns:
            Dictionary with keywords as keys, each containing:
                - 'top': DataFrame of top related queries
                - 'rising': DataFrame of rising related queries

        Example:
            >>> pytrends.build_payload(['Python'])
            >>> queries = pytrends.related_queries()
            >>> print(queries['Python']['top'].head())
        """
        # Browser mode: capture relatedsearches QUERY API response
        if self.browser_mode:
            if len(self.kw_list) != 1:
                raise exceptions.InvalidParameterError(
                    "Browser mode only supports 1 keyword"
                )
            
            keyword = self.kw_list[0]
            
            # Capture all responses if not already cached
            if not self.browser_responses_cache:
                self._capture_all_api_responses(keyword)
            
            # Get cached response
            response_data = self.browser_responses_cache.get('related_queries')
            
            if not response_data:
                raise exceptions.ResponseError("Failed to capture related_queries API response")
            
            return {keyword: self._parse_relatedsearches_response(response_data)}
        
        # Standard mode
        if not self.related_queries_widget_list:
            raise exceptions.ResponseError(
                "No related queries widgets available. Call build_payload() first."
            )

        result_dict = {}

        for widget in self.related_queries_widget_list:
            # Extract keyword
            try:
                kw = widget["request"]["restriction"]["complexKeywordsRestriction"]["keyword"][0][
                    "value"
                ]
            except (KeyError, IndexError):
                kw = ""

            # Build payload
            payload = {
                "req": json.dumps(widget["request"]),
                "token": widget["token"],
                "tz": self.tz,
            }

            # Get data
            req_json = self._get_data(
                url=RELATED_QUERIES_URL,
                method=self.GET_METHOD,
                trim_chars=5,
                params=payload,
            )

            # Parse top queries
            try:
                top_df = pd.DataFrame(req_json["default"]["rankedList"][0]["rankedKeyword"])
                top_df = top_df[["query", "value"]]
            except (KeyError, IndexError):
                top_df = None

            # Parse rising queries
            try:
                rising_df = pd.DataFrame(req_json["default"]["rankedList"][1]["rankedKeyword"])
                rising_df = rising_df[["query", "value"]]
            except (KeyError, IndexError):
                rising_df = None

            result_dict[kw] = {"top": top_df, "rising": rising_df}

        return result_dict

    def trending_searches(self, pn: str = "united_states") -> pd.DataFrame:
        """
        Get trending searches for a country

        Args:
            pn: Country name (e.g., 'united_states', 'united_kingdom')

        Returns:
            DataFrame of trending searches

        Example:
            >>> pytrends = TrendReq()
            >>> df = pytrends.trending_searches(pn='united_states')
            >>> print(df.head())
        """
        req_json = self._get_data(url=TRENDING_SEARCHES_URL, method=self.GET_METHOD)

        if pn not in req_json:
            raise exceptions.InvalidParameterError(
                f"Country '{pn}' not found. Available: {list(req_json.keys())}"
            )

        return pd.DataFrame(req_json[pn])

    def today_searches(self, pn: str = "US") -> pd.DataFrame:
        """
        Get today's trending searches (Daily Trends)

        Args:
            pn: Country code (e.g., 'US', 'GB')

        Returns:
            DataFrame of today's trending searches

        Example:
            >>> pytrends = TrendReq()
            >>> df = pytrends.today_searches(pn='US')
            >>> print(df.head())
        """
        params = {"ns": 15, "geo": pn, "tz": "-180", "hl": self.hl}

        req_json = self._get_data(
            url=TODAY_SEARCHES_URL,
            method=self.GET_METHOD,
            trim_chars=5,
            params=params,
        )

        try:
            trends = req_json["default"]["trendingSearchesDays"][0]["trendingSearches"]
            result_df = pd.DataFrame([trend["title"] for trend in trends])
            return result_df.iloc[:, -1]
        except (KeyError, IndexError):
            return pd.DataFrame()

    def realtime_trending_searches(
        self, pn: str = "US", cat: str = "all", count: int = 300
    ) -> pd.DataFrame:
        """
        Get real-time trending searches

        Args:
            pn: Country code (e.g., 'US', 'GB')
            cat: Category ('all' or specific category)
            count: Maximum number of results (max 300)

        Returns:
            DataFrame of real-time trending searches with entity names and titles
        """
        # Validate count
        ri_value = min(count, 300)
        rs_value = min(count - 1, 200)

        params = {
            "ns": 15,
            "geo": pn,
            "tz": "300",
            "hl": self.hl,
            "cat": cat,
            "fi": "0",
            "fs": "0",
            "ri": ri_value,
            "rs": rs_value,
            "sort": 0,
        }

        req_json = self._get_data(
            url=REALTIME_TRENDING_SEARCHES_URL,
            method=self.GET_METHOD,
            trim_chars=5,
            params=params,
        )

        try:
            trending_stories = req_json["storySummaries"]["trendingStories"]

            # Extract only wanted keys
            wanted_keys = ["entityNames", "title"]
            filtered_data = [
                {key: ts[key] for key in wanted_keys if key in ts} for ts in trending_stories
            ]

            return pd.DataFrame(filtered_data)
        except KeyError:
            return pd.DataFrame()

    def top_charts(
        self, date: int, hl: str = "en-US", tz: int = 300, geo: str = "GLOBAL"
    ) -> Optional[pd.DataFrame]:
        """
        Get top charts for a specific year

        Args:
            date: Year (e.g., 2023, 2024)
            hl: Language
            tz: Timezone offset
            geo: Geographic location

        Returns:
            DataFrame of top charts, or None if not available

        Example:
            >>> pytrends = TrendReq()
            >>> df = pytrends.top_charts(date=2024, geo='US')
            >>> print(df.head())
        """
        # Validate date
        try:
            date = int(date)
        except (ValueError, TypeError):
            raise ValueError("date must be a year in format YYYY")

        params = {"hl": hl, "tz": tz, "date": date, "geo": geo, "isMobile": False}

        req_json = self._get_data(
            url=TOP_CHARTS_URL,
            method=self.GET_METHOD,
            trim_chars=5,
            params=params,
        )

        try:
            return pd.DataFrame(req_json["topCharts"][0]["listItems"])
        except (KeyError, IndexError):
            return None

    def suggestions(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Get keyword suggestions from Google Trends autocomplete

        Args:
            keyword: Search keyword

        Returns:
            List of suggestion dictionaries

        Example:
            >>> pytrends = TrendReq()
            >>> suggestions = pytrends.suggestions('python')
            >>> for s in suggestions:
            ...     print(s['title'])
        """
        kw_param = quote(keyword)
        params = {"hl": self.hl}

        req_json = self._get_data(
            url=SUGGESTIONS_URL + kw_param,
            params=params,
            method=self.GET_METHOD,
            trim_chars=5,
        )

        return req_json.get("default", {}).get("topics", [])

    def categories(self) -> Dict[str, Any]:
        """
        Get available category data from Google Trends

        Returns:
            Dictionary of available categories

        Example:
            >>> pytrends = TrendReq()
            >>> cats = pytrends.categories()
            >>> print(cats)
        """
        params = {"hl": self.hl}

        return self._get_data(
            url=CATEGORIES_URL,
            params=params,
            method=self.GET_METHOD,
            trim_chars=5,
        )

    def trending_analysis_topics(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get trending analysis topics from the Google Trends Explore page
        without a specific query keyword. Returns top and rising topics.

        Browser mode only — navigates to the Explore page and captures the
        relatedsearches (ENTITY) API response via network interception.

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m', 'today 12-m')
            geo: Country code (e.g. 'RU', 'KZ', 'US'). Empty = worldwide.
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('' for web, 'youtube', 'news', etc.)

        Returns:
            Dictionary with 'top' and 'rising' DataFrames of trending topics.
            Each topic has: topic_mid, topic_title, topic_type, value, link.

        Example:
            >>> config = BrowserConfig(headless=False)
            >>> pytrends = TrendReq(browser_config=config)
            >>> result = pytrends.trending_analysis_topics(
            ...     timeframe='now 7-d', geo='RU', hl='ru', gprop='youtube'
            ... )
            >>> print(result['top'].head())
        """
        if not self.browser_mode:
            raise exceptions.BrowserError(
                "trending_analysis_topics() requires browser mode. "
                "Pass BrowserConfig to TrendReq()."
            )

        if not self.browser_responses_cache.get('related_topics'):
            self._capture_analysis_responses(timeframe, geo, hl, gprop)

        response_data = self.browser_responses_cache.get('related_topics')

        if not response_data:
            self._capture_analysis_responses(timeframe, geo, hl, gprop)
            response_data = self.browser_responses_cache.get('related_topics')

        if not response_data:
            raise exceptions.ResponseError(
                "Failed to capture trending analysis topics response"
            )

        return self._parse_relatedsearches_response(response_data)

    def trending_analysis_queries(
        self,
        timeframe: str = "today 1-m",
        geo: str = "",
        hl: str = "en",
        gprop: str = "",
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get trending analysis queries from the Google Trends Explore page
        without a specific query keyword. Returns top and rising queries.

        Browser mode only — navigates to the Explore page and captures the
        relatedsearches (QUERY) API response via network interception.

        Args:
            timeframe: Time range (e.g. 'now 7-d', 'today 1-m', 'today 12-m')
            geo: Country code (e.g. 'RU', 'KZ', 'US'). Empty = worldwide.
            hl: Language code (e.g. 'en', 'ru')
            gprop: Google property ('' for web, 'youtube', 'news', etc.)

        Returns:
            Dictionary with 'top' and 'rising' DataFrames of trending queries.
            Each query has: query, value, link.

        Example:
            >>> config = BrowserConfig(headless=False)
            >>> pytrends = TrendReq(browser_config=config)
            >>> result = pytrends.trending_analysis_queries(
            ...     timeframe='now 7-d', geo='RU', hl='ru', gprop='youtube'
            ... )
            >>> print(result['top'].head())
        """
        if not self.browser_mode:
            raise exceptions.BrowserError(
                "trending_analysis_queries() requires browser mode. "
                "Pass BrowserConfig to TrendReq()."
            )

        if not self.browser_responses_cache.get('related_queries'):
            self._capture_analysis_responses(timeframe, geo, hl, gprop)

        response_data = self.browser_responses_cache.get('related_queries')

        if not response_data:
            self._capture_analysis_responses(timeframe, geo, hl, gprop)
            response_data = self.browser_responses_cache.get('related_queries')

        if not response_data:
            raise exceptions.ResponseError(
                "Failed to capture trending analysis queries response"
            )

        return self._parse_relatedsearches_response(response_data)
