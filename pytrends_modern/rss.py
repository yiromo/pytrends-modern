"""
RSS Feed module for fast real-time Google Trends data
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

import pandas as pd
import requests

from pytrends_modern.config import COUNTRIES, US_STATES
from pytrends_modern.exceptions import DownloadError, InvalidParameterError

# Type aliases
OutputFormat = Literal["dict", "json", "csv", "dataframe"]


class TrendsRSS:
    """
    Google Trends RSS Feed API

    Fast access to real-time trending searches with rich media.

    Features:
    - 0.2 second response time
    - News articles and headlines
    - Images for each trend
    - Traffic volume data
    - Multiple output formats

    Example:
        >>> rss = TrendsRSS()
        >>> trends = rss.get_trends(geo='US')
        >>> for trend in trends:
        ...     print(f"{trend['title']}: {trend['traffic']}")
    """

    RSS_URL_TEMPLATE = "https://trends.google.com/trending/rss?geo={geo}"

    def __init__(self, timeout: int = 10):
        """
        Initialize TrendsRSS client

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def _validate_geo(self, geo: str) -> str:
        """
        Validate geographic parameter

        Args:
            geo: Country or US state code

        Returns:
            Validated geo code (uppercase)

        Raises:
            InvalidParameterError: If geo is invalid
        """
        geo = geo.upper()

        if geo in COUNTRIES or geo in US_STATES:
            return geo

        # Suggest similar matches
        all_geos = list(COUNTRIES.keys()) + list(US_STATES.keys())
        similar = [code for code in all_geos if code.startswith(geo[0]) if len(geo) > 0][:5]

        error_msg = f"Invalid geo code '{geo}'."
        if similar:
            error_msg += f" Did you mean: {', '.join(similar)}?"
        error_msg += f"\n\nAvailable: {len(COUNTRIES)} countries, {len(US_STATES)} US states"
        error_msg += "\nExamples: 'US', 'GB', 'CA', 'US-CA', 'US-NY'"

        raise InvalidParameterError(error_msg)

    def _parse_rss_feed(
        self,
        xml_content: str,
        include_images: bool = True,
        include_articles: bool = True,
        max_articles_per_trend: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Parse RSS XML feed into structured data

        Args:
            xml_content: Raw XML content
            include_images: Include trend images
            include_articles: Include news articles
            max_articles_per_trend: Maximum articles per trend

        Returns:
            List of trend dictionaries
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise DownloadError(f"Failed to parse RSS feed: {str(e)}")

        trends = []

        # Parse each item (trend)
        for item in root.findall(".//item"):
            trend_data: Dict[str, Any] = {}

            # Basic info
            trend_data["title"] = self._get_text(item, "title")
            trend_data["description"] = self._get_text(item, "description")
            trend_data["link"] = self._get_text(item, "link")
            trend_data["pub_date"] = self._get_text(item, "pubDate")

            # Parse pubDate to datetime
            if trend_data["pub_date"]:
                try:
                    trend_data["pub_date_datetime"] = datetime.strptime(
                        trend_data["pub_date"], "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    trend_data["pub_date_datetime"] = None

            # Traffic volume (from ht:approx_traffic namespace)
            traffic_elem = item.find(".//{https://trends.google.com/trending/rss}approx_traffic")
            if traffic_elem is not None and traffic_elem.text:
                # Remove '+' and ',' from traffic string
                traffic_str = traffic_elem.text.replace("+", "").replace(",", "")
                try:
                    trend_data["traffic"] = int(traffic_str)
                except ValueError:
                    trend_data["traffic"] = traffic_elem.text
            else:
                trend_data["traffic"] = None

            # Image
            if include_images:
                picture_elem = item.find(".//{https://trends.google.com/trending/rss}picture")
                trend_data["picture"] = picture_elem.text if picture_elem is not None else None

            # News articles
            if include_articles:
                news_items = item.findall(".//{https://trends.google.com/trending/rss}news_item")
                articles = []

                for news_item in news_items[:max_articles_per_trend]:
                    article: Dict[str, Any] = {}

                    # Article title
                    title_elem = news_item.find(
                        ".//{https://trends.google.com/trending/rss}news_item_title"
                    )
                    article["title"] = title_elem.text if title_elem is not None else None

                    # Article URL
                    url_elem = news_item.find(
                        ".//{https://trends.google.com/trending/rss}news_item_url"
                    )
                    article["url"] = url_elem.text if url_elem is not None else None

                    # Article snippet
                    snippet_elem = news_item.find(
                        ".//{https://trends.google.com/trending/rss}news_item_snippet"
                    )
                    article["snippet"] = snippet_elem.text if snippet_elem is not None else None

                    # Article source
                    source_elem = news_item.find(
                        ".//{https://trends.google.com/trending/rss}news_item_source"
                    )
                    article["source"] = source_elem.text if source_elem is not None else None

                    articles.append(article)

                trend_data["articles"] = articles
                trend_data["article_count"] = len(articles)

            trends.append(trend_data)

        return trends

    def _get_text(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely extract text from XML element"""
        elem = element.find(tag)
        return elem.text if elem is not None else None

    def get_trends(
        self,
        geo: str = "US",
        output_format: OutputFormat = "dict",
        include_images: bool = True,
        include_articles: bool = True,
        max_articles_per_trend: int = 5,
    ) -> Union[List[Dict], str, pd.DataFrame]:
        """
        Get trending searches from RSS feed

        Args:
            geo: Country or US state code (e.g., 'US', 'GB', 'US-CA')
            output_format: Output format ('dict', 'json', 'csv', 'dataframe')
            include_images: Include trend images
            include_articles: Include news articles
            max_articles_per_trend: Maximum articles per trend

        Returns:
            Trends data in specified format

        Raises:
            InvalidParameterError: If parameters are invalid
            DownloadError: If download fails

        Example:
            >>> rss = TrendsRSS()
            >>> trends = rss.get_trends(geo='US', output_format='dataframe')
            >>> print(trends.head())
        """
        # Validate geo
        geo = self._validate_geo(geo)

        # Build URL
        url = self.RSS_URL_TEMPLATE.format(geo=geo)

        # Fetch RSS feed
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DownloadError(f"Failed to download RSS feed: {str(e)}")

        # Parse feed
        trends = self._parse_rss_feed(
            response.text,
            include_images=include_images,
            include_articles=include_articles,
            max_articles_per_trend=max_articles_per_trend,
        )

        # Format output
        return self._format_output(trends, output_format)

    def _format_output(
        self, trends: List[Dict[str, Any]], output_format: OutputFormat
    ) -> Union[List[Dict], str, pd.DataFrame]:
        """
        Format trends data to specified output format

        Args:
            trends: List of trend dictionaries
            output_format: Desired output format

        Returns:
            Formatted data
        """
        if output_format == "dict":
            return trends

        elif output_format == "json":
            import json

            return json.dumps(trends, indent=2, default=str)

        elif output_format == "dataframe":
            # Flatten nested articles for DataFrame
            flattened_trends = []
            for trend in trends:
                flat_trend = {
                    "title": trend.get("title"),
                    "description": trend.get("description"),
                    "link": trend.get("link"),
                    "pub_date": trend.get("pub_date"),
                    "traffic": trend.get("traffic"),
                    "picture": trend.get("picture"),
                    "article_count": trend.get("article_count", 0),
                }
                flattened_trends.append(flat_trend)

            return pd.DataFrame(flattened_trends)

        elif output_format == "csv":
            # Convert to DataFrame then CSV
            df = self._format_output(trends, "dataframe")
            return df.to_csv(index=False)

        else:
            raise InvalidParameterError(
                f"Invalid output format '{output_format}'. "
                "Must be one of: 'dict', 'json', 'csv', 'dataframe'"
            )

    def get_available_geos(self) -> Dict[str, str]:
        """
        Get dictionary of available geographic locations

        Returns:
            Dictionary mapping geo codes to location names

        Example:
            >>> rss = TrendsRSS()
            >>> geos = rss.get_available_geos()
            >>> print(f"Available countries: {len([g for g in geos if '-' not in g])}")
        """
        return {**COUNTRIES, **US_STATES}

    def get_trends_for_multiple_geos(
        self, geos: List[str], output_format: OutputFormat = "dict", **kwargs: Any
    ) -> Dict[str, Union[List[Dict], str, pd.DataFrame]]:
        """
        Get trends for multiple geographic locations

        Args:
            geos: List of geo codes
            output_format: Output format for each geo
            **kwargs: Additional arguments passed to get_trends()

        Returns:
            Dictionary mapping geo codes to their trends

        Example:
            >>> rss = TrendsRSS()
            >>> trends = rss.get_trends_for_multiple_geos(
            ...     geos=['US', 'GB', 'CA'],
            ...     output_format='dataframe'
            ... )
            >>> for geo, df in trends.items():
            ...     print(f"{geo}: {len(df)} trends")
        """
        results = {}

        for geo in geos:
            try:
                results[geo] = self.get_trends(geo=geo, output_format=output_format, **kwargs)
            except Exception as e:
                print(f"[WARN] Failed to get trends for {geo}: {str(e)}")
                results[geo] = [] if output_format == "dict" else None

        return results
