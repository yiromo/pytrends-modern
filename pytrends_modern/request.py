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
        """
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

        # Get initial cookies
        self.cookies = self._get_google_cookie()

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

    def _get_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(USER_AGENTS) if self.rotate_user_agent else USER_AGENTS[0]

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

        # Get tokens from Google
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
            df = df.fillna(False)
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

        Example:
            >>> pytrends = TrendReq()
            >>> df = pytrends.realtime_trending_searches(pn='US', count=50)
            >>> print(df.head())
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
