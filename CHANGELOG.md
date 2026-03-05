# Changelog

All notable changes to pytrends-modern will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.5] - 2026-03-06

### Added
- 📺 **YouTube Search Support** - Get trends from YouTube searches
  - `youtube=True` in `BrowserConfig` to search YouTube instead of Google Search
  - Adds `gprop=youtube` to the Trends URL
  - Works with both sync `TrendReq` and async `AsyncTrendReq`
  - Worldwide + past 30 days by default
  - Combinable with `timeframe='today 12-m'` for longer ranges

## [0.2.4] - 2026-01-16

### Added
- 📅 **Timeframe Support** - Choose between different time ranges
  - `timeframe='today 1-m'` - Past month (default)
  - `timeframe='today 12-m'` - Past 12 months
  - Works with both sync `TrendReq` and async `AsyncTrendReq`
  - New example: `examples/test_timeframes.py`

### Changed
- Updated browser mode URL building to support configurable timeframes
- Removed hardcoded timeframe limitation from documentation

## [0.2.3] - 2026-01-16

### Added
- 🛡️ **Anti-Rate-Limit Features** - Prevent 429 errors with browser mode
  - `min_delay`/`max_delay` parameters for random delays between requests (default: 2-5s)
  - `persistent_context` option to use fresh profile each run (default: True)
  - `custom_config` parameter for advanced Camoufox configuration
  - Automatic fingerprint randomization via Camoufox's BrowserForge integration
  - New example: `test_rate_limit_fix.py` showing anti-rate-limit configuration

### Changed
- Removed manual BrowserForge fingerprint generation (Camoufox handles it automatically)
- Updated documentation with anti-rate-limit best practices

### Fixed
- Fixed 429 rate limiting issues when making repeated requests with browser mode

## [0.2.2] - 2026-01-14

### Added
- 🐳 **Docker Support** - Enhanced headless mode for containers
  - `headless="virtual"` option for Docker/containerized environments
  - Uses Xvfb virtual display to prevent display errors in containers
  - New example: `examples/example_docker_usage.py`

### Changed
- `BrowserConfig.headless` now accepts `Union[bool, str]` (was `bool`)
- Updated README with Docker headless options documentation

## [0.2.1] - 2026-01-14

### Added
- 🚀 **Async/Await Support** - New `AsyncTrendReq` class for async operations
  - Full async/await support using `async with AsyncTrendReq()` context manager
  - Uses `camoufox.async_api.AsyncCamoufox` for async browser operations
  - All 4 API methods now available as async: `await pytrends.interest_over_time()`, etc.
  - Same persistent profile system as sync version
  - Same network interception and response caching
  - Reuses parsing logic from sync `TrendReq` class
- 🐳 **Docker Support** - Enhanced headless mode options for containers
  - `headless="virtual"` option for Docker/containerized environments
  - Uses Xvfb virtual display to prevent display errors in containers
  - `headless=False` for local development (show browser)
  - `headless=True` for standard headless mode
  - New example: `examples/example_docker_usage.py`

### Fixed
- Fixed async response.body() handling in network interception (must be awaited)

## [0.2.0] - 2026-01-12

### Added
- 🦊 **Camoufox Browser Mode** - Bypass Google's rate limits using your Google account
  - Full Camoufox integration with advanced fingerprinting (no bot detection!)
  - Persistent profile support - log in once, reuse forever
  - Network interception to capture all 4 Google Trends APIs
  - New `BrowserConfig` class for Camoufox configuration
  - New `camoufox_setup` module for easy Google account setup
  - Command-line setup tool: `python -m pytrends_modern.camoufox_setup`
  - Profile status checker: `python -m pytrends_modern.camoufox_setup status`
  - Browser mode works with: `interest_over_time()`, `interest_by_region()`, `related_topics()`, `related_queries()`
  - Requires `camoufox[geoip]>=0.4.11` and `browserforge[all]>=1.0.0`
  
### Changed
- **BREAKING**: Browser mode now requires profile configuration before first use
  - Users must run `setup_profile()` or command-line setup to log in to Google
  - Profile check added to `TrendReq._init_camoufox()` - raises `BrowserError` if not configured
  - Persistent profile directory: `~/.config/camoufox-pytrends-profile`
- Replaced DrissionPage with Camoufox for superior anti-detection
- Browser mode limitations documented:
  - Only 1 keyword (no comparisons)
  - Only 'today 1-m' timeframe
  - Only WORLDWIDE region
  - But NO rate limits with Google account login!

### Fixed
- Fixed JSONP prefix removal in response parser (5 bytes not 4)
- Fixed URL decoding for relatedsearches API keywordType detection
- Fixed Camoufox context manager usage with `__enter__()` and `__exit__()`
- Fixed 2-tab issue by reusing existing page instead of creating new one
- Network interception now correctly caches all 4 API responses

### Technical Details
- Network interception via Playwright's `page.on("response")` event handler
- Responses cached by API type: `interest_over_time`, `interest_by_region`, `related_topics`, `related_queries`
- URL-encoded parameters decoded to detect `keywordType` in relatedsearches URLs
- Profile validation checks for Firefox profile files: `prefs.js`, `cookies.sqlite`, `storage`

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
