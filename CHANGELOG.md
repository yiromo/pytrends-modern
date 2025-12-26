# Changelog

All notable changes to pytrends-modern will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-12-26

### Added
- 🚀 **Selenium-based scraper for deprecated endpoints** - `TrendsScraper` class
  - `trending_searches()` - Download trending searches via Selenium (replaces broken API)
  - `today_searches()` - Convenience method for 24-hour trends
  - `realtime_trending_searches()` - Convenience method for real-time trends (4-hour default)
  - Supports categories, time periods (4h, 24h, 48h, 168h), active-only filtering
  - Returns pandas DataFrame with 6 columns: Trends, Search volume, Started, Ended, Trend breakdown, Explore link
  - Headless Chrome automation with automatic driver management
  - Thanks to [trendspyg](https://github.com/flack0x/trendspyg) for the proven Selenium approach
- Added `selenium>=4.0.0` and `webdriver-manager>=3.8.0` as dependencies

### Fixed
- 🎉 **RSS endpoint is working again!** Updated RSS implementation with new Google Trends URL
  - Changed RSS_URL_TEMPLATE from old daily RSS to new trending RSS endpoint
  - Updated XML namespace from `http://www.google.com/trends/hottrends` to `https://trends.google.com/trending/rss`
  - Fixed all XML element parsing to use correct namespace
  - `TrendsRSS.get_trends()` now returns data in ~0.7 seconds!
  - Old URL: `https://trends.google.com/trends/trendingsearches/daily/rss` (404)
  - New URL: `https://trends.google.com/trending/rss` (✅ working)
  - Thanks to [trendspyg](https://github.com/flack0x/trendspyg) for the updated URL pattern
- Fixed pandas FutureWarning for fillna downcasting by using `.where()` instead of `.fillna()`
- Removed Selenium usage warning - users can choose their preferred method
- Fixed browser cleanup errors during Python shutdown in `TrendsScraper`

### Changed
- Google's trending API endpoints are deprecated, but alternatives now available:
  - **Fast option**: `TrendsRSS.get_trends()` - RSS feed, 0.7s response, 10 trends
  - **Full option**: `TrendsScraper.trending_searches()` - Selenium scraping, ~15s, 400+ trends
- Export button detection updated to use "Export" instead of "Download" (Google UI change)

## [0.1.1] - 2025-12-26

### Fixed
- Renamed package directory from `pytrends_plus` to `pytrends_modern` for consistency
- Updated all internal imports and references

## [0.1.0] - 2025-12-26

### Added
- Initial release of pytrends-modern
- Core Google Trends API functionality from pytrends
  - `interest_over_time()` - Get historical search interest
  - `interest_by_region()` - Get geographic distribution
  - `related_topics()` - Get related topics
  - `related_queries()` - Get related search queries
  - `trending_searches()` - Get current trending searches
  - `today_searches()` - Get daily trends
  - `realtime_trending_searches()` - Get real-time trends
  - `top_charts()` - Get top charts for a year
  - `suggestions()` - Get keyword suggestions
  - `categories()` - Get available categories
- RSS feed support for fast real-time trending data
  - 0.2 second response time vs 10+ seconds for full scraping
  - Rich media: images, news articles, headlines
  - Multiple geographic locations supported (125+ countries)
- Enhanced error handling and retry logic
  - Automatic retries with exponential backoff
  - Rate limit detection and management
  - Proxy rotation support
  - Better error messages
- Modern Python features
  - Full type hints throughout
  - Dataclasses for structured data
  - Modern exception handling
  - Python 3.8+ support
- Command-line interface (CLI)
  - `pytrends-modern interest` - Get interest over time
  - `pytrends-modern region` - Get interest by region
  - `pytrends-modern rss` - Get RSS trends
  - `pytrends-modern suggest` - Get keyword suggestions
  - `pytrends-modern trending` - Get trending searches
  - Rich terminal output with tables and colors
- Multiple export formats
  - CSV, JSON, Parquet, Excel
  - DataFrame output
- Utility functions
  - Date/timeframe conversion
  - Trend momentum calculation
  - Spike detection
  - Multi-format export
  - Keyword validation
- Comprehensive documentation
  - README with quick start guide
  - API documentation
  - Usage examples (basic and advanced)
  - CLI documentation
- Test suite
  - Unit tests for core functionality
  - Integration tests (marked separately)
  - Fixtures for testing

### Changed
- Improved cookie handling from pytrends
- Better proxy rotation logic
- More robust JSON parsing
- Enhanced widget token retrieval

### Fixed
- Cookie retrieval errors
- Proxy error handling
- JSON parsing edge cases
- Empty response handling

## [Future Plans]

### Planned for 1.1.0
- Async support with `AsyncTrendReq` class
- Selenium integration for advanced scraping
- Daily data collection with retry logic
- Historical hourly interest data
- Batch processing utilities
- Rate limit queue management
- Cache support for repeated queries

### Planned for 1.2.0
- Web dashboard for visualization
- Data analysis utilities
- Export to database (SQLite, PostgreSQL)
- Scheduled data collection
- Webhook notifications
- API server mode

### Planned for 2.0.0
- Complete async/await API
- Plugin system for custom data sources
- Machine learning trend predictions
- Advanced visualization tools
- Multi-language support
- Cloud deployment options
