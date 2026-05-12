# Changelog

All notable changes to pytrends-modern will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.8] - 2026-05-13

### Added
- **SVG Graph Scraping Fallback** — when Google returns 429/500 and the API network
  responses are empty, `interest_over_time()` now automatically falls back to scraping
  the SVG chart rendered in the browser. Parses the `<path d="M...">` coordinates and
  maps them to dates/values using chart bounds and axis labels. Works for all timeframes
  (past hour, past day, past month, past 12 months, past 5 years) and search types
  (Google Search, YouTube, etc.). Both sync and async modes supported.

## [0.2.7] - 2026-05-12

### Fixed
- **Async sign-in coroutines not awaited** — `AsyncTrendReq` called sync Playwright helpers
  (`_find_sign_in_button`, `_click_sign_in_button`, etc.) on async page objects, causing
  `RuntimeWarning: coroutine 'Locator.count' was never awaited` and silent sign-in failure.
  Added 6 async counterparts (`_afind_sign_in_button`, `_aclick_sign_in_button`,
  `_aclick_first_account`, `_afill_password`, `_aclick_next_button`, `auto_google_sign_in_async`)
  that properly `await` all Playwright locator methods.
- `AsyncTrendReq._ensure_signed_in()` now uses `auto_google_sign_in_async()`
- `AsyncTrendReq._capture_all_api_responses()` now uses `await _afind_sign_in_button()`

### Changed
- All browser mode URLs now include `&legacy` parameter to force the legacy Google Trends UI
  for more reliable API responses. Affects sync and async modes, setup, and test.

## [0.2.6] - 2026-05-11

### Added
- **Auto Google Sign-In** — fully automated login flow when `google_sign_in=True`
  - Detects "Sign in" / "Anmelden" / "Войти" button on Google Trends (CSS + XPath fallback)
  - Clicks sign-in, selects first account, enters password, clicks "Next"
  - Password from `BrowserConfig(google_password=...)` or `GOOGLE_ACC_PASSWORD` env var
  - Works in both sync `TrendReq` and async `AsyncTrendReq`
  - Auto re-authenticates if session expires during a run
  - Profile auto-created on first use — no manual `setup_profile()` required
  - CLI: `python -m pytrends_modern.camoufox_setup auto-signin --password ...`
- `ConfigurationError` exception class for missing password/config errors
- `example_auto_signin.py` example with all usage patterns

### Changed
- `_init_camoufox()` no longer raises `BrowserError` when profile is missing if `google_sign_in=True` — creates and configures profile automatically
- `_capture_all_api_responses()` now checks for expired sessions and re-signs in when `google_sign_in=True`
- CLI rewritten with `argparse` subcommands instead of manual `sys.argv` parsing
- `setup_profile()` accepts `google_sign_in` and `google_password` parameters

## [0.2.5] - 2026-03-06

### Added
- **YouTube Search Support** — `youtube=True` in `BrowserConfig` to search YouTube instead of Google Search

## [0.2.4] - 2026-02-06

### Added
- **Timeframe Support** — choose `today 1-m` (default) or `today 12-m` in `BrowserConfig`

### Changed
- Browser mode URL building now supports configurable timeframes (was hardcoded to `today 1-m`)

## [0.2.3] - 2026-01-16

### Added
- **Anti-Rate-Limit Features** — `min_delay`/`max_delay` for random delays, `persistent_context` option, `custom_config` for advanced Camoufox settings

### Changed
- Removed manual BrowserForge fingerprint generation (Camoufox handles it automatically)

## [0.2.2] - 2026-01-14

### Added
- **Docker Support** — `headless="virtual"` option using Xvfb virtual display

### Changed
- `BrowserConfig.headless` now accepts `Union[bool, str]`

## [0.2.1] - 2026-01-14

### Added
- **Async Support** — `AsyncTrendReq` class using `camoufox.async_api.AsyncCamoufox`
  - Async context manager: `async with AsyncTrendReq(browser_config=config) as pytrends:`
  - All 4 browser-mode API methods available as async

## [0.2.0] - 2026-01-12

### Added
- **Camoufox Browser Mode** — bypass Google's rate limits using anti-detection fingerprinting and Google account login
  - Persistent profile support (log in once, reuse forever)
  - Network interception to capture all 4 Google Trends API responses
  - `BrowserConfig` class for Camoufox configuration
  - `camoufox_setup` module with CLI for profile management
  - Requires `camoufox[geoip]>=0.4.11` and `browserforge[all]>=1.0.0`

### Changed
- **BREAKING**: Browser mode requires profile configuration before first use

### Fixed
- JSONP prefix removal in response parser (5 bytes not 4)
- URL decoding for relatedsearches API keywordType detection
- Camoufox context manager usage
- 2-tab issue by reusing existing page

## [0.1.2] - 2025-12-26

### Added
- **Selenium Scraper** — `TrendsScraper` class for downloading trending data via browser automation
  - `trending_searches()`, `today_searches()`, `realtime_trending_searches()`
  - Supports categories, time periods, headless mode

### Fixed
- **RSS endpoint** — updated URL from deprecated `trendingsearches/daily/rss` (404) to working `trending/rss`
- XML namespace updated to `https://trends.google.com/trending/rss`
- pandas FutureWarning for fillna downcasting

## [0.1.1] - 2025-12-26

### Fixed
- Renamed package directory from `pytrends_plus` to `pytrends_modern`

## [0.1.0] - 2025-12-26

### Added
- Initial release
- Core Google Trends API: `interest_over_time()`, `interest_by_region()`, `related_topics()`, `related_queries()`, `trending_searches()`, `today_searches()`, `realtime_trending_searches()`, `top_charts()`, `suggestions()`, `categories()`
- RSS feed support with rich media (images, articles, traffic)
- Enhanced error handling with automatic retries, rate limit detection, proxy rotation
- Full type hints, Python 3.8+
- CLI with Rich terminal output
- Utility functions: date conversion, trend momentum, spike detection, multi-format export
