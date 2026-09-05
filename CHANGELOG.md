# Changelog

All notable changes to pytrends-modern will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.13] - 2026-09-06

### Fixed
- **Stale browser-mode cache across keywords.** `browser_responses_cache` was
  keyed only by response type, so after `build_payload(['Python'])` a later
  `build_payload(['Rust'])` + `interest_over_time()` skipped navigation and
  returned Python's series under a `Rust` column. The init-time sign-in
  navigation (`q=Python`) also pre-filled the cache, so the first call for any
  other keyword returned Python's data. Captures are now tagged with a
  signature (`("explore", keyword)`) and every data method re-navigates when
  the signature or key does not match. Sync and async.
- **`trending_analysis_*()` ignored their arguments once anything was cached.**
  They shared the `related_topics`/`related_queries` keys with the keyword
  methods, so `trending_analysis_merged(geo='RU', gprop='youtube')` followed by
  `trending_analysis_topics(geo='KZ')` returned the RU/YouTube data labelled
  KZ (and vice versa with `related_topics()`). Analysis captures now use the
  signature `("analysis", timeframe, geo, hl, gprop)`.
- **`requests_args` crashed with `TypeError`.** Passing the documented extra
  kwargs (`timeout`, `cookies`, `params`, `headers`) collided with explicit
  keyword arguments in `_get_data()` / `_get_google_cookie()`. Arguments are
  now merged once, with user values taking precedence.
- **`TrendsScraper.close()` could delete a user-supplied directory.** It
  decided whether to `rmtree` the download dir by testing `'/tmp/'` in the
  path, so `download_dir='/tmp/exports'` was wiped on exit while auto-created
  temp dirs on macOS/Windows (`/var/folders/...`, `...\Temp`) leaked. It now
  removes only a directory it created itself.
- **Identifier-page email fallback (0.2.12) was unreachable.**
  `_click_first_account()`'s last-resort "click the first `ul li`" matched
  footer links on Google's email page and returned `True`, so `_fill_email()`
  never ran and sign-in failed later with a misleading password error. The
  helper now returns `False` when an identifier input is present. Sync and async.
- **`import_profile()` destroyed the working profile on a bad archive.** The
  existing profile was `rmtree`'d before the extracted content was validated.
  Validation now happens first; an archive without a profile leaves the
  current one untouched.
- **`TrendsRSS.get_trends(geo='')` raised `IndexError`** instead of
  `InvalidParameterError` (comprehension indexed `geo[0]` before the length
  guard).
- **SVG fallback produced year-1900 dates for short timeframes.** Time-only
  x-axis labels (`'6:00 AM'`) were parsed as `1900-01-01`; the new
  `_parse_axis_dates()` accepts only full-date labels, sorts them, and falls
  back to `_timeframe_to_dates()` otherwise. Sync and async.
- **`persistent_context=False` still required an on-disk profile** even though
  `user_data_dir` is passed as `None` in that mode. The profile check now
  applies only when `persistent_context=True`.
- `today_searches()` is annotated and returns `pd.Series` on both paths;
  `_parse_comparedgeo_response()` puts `geoCode` first, matching the HTTP path.

### Added
- **`google_email` in `setup_profile()`, `--email/-e` on the `auto-signin` CLI,
  and `GOOGLE_ACC_EMAIL` env fallback**, so the identifier-page recovery
  documented in 0.2.12 also works from the command line.
- `auto-signin --headless` now fails fast when auto sign-in cannot complete
  instead of blocking on `input()` waiting for a manual login.
- `config.EXPLORE_URL` constant for the Explore page.

### Changed
- **JSONP prefix handling unified** in `utils.strip_jsonp_prefix()` (str or
  bytes, regex over every `)]}'` / `)]}',` / whitespace variant). Replaces the
  per-endpoint `trim_chars` counts in the HTTP path and the hand-rolled prefix
  chains in both browser response handlers; the dead `_parse_api_response()`
  (with its `")]},"` typo) is removed.
- Browser captures replace fixed `time.sleep()` / `asyncio.sleep()` waits with
  `_wait_for_cached_keys()`, which polls for the expected response keys via
  `page.wait_for_timeout()` (5 s explore / 8 s analysis) and returns as soon
  as they arrive. In sync mode this also lets Playwright dispatch response
  events, which a plain `time.sleep()` blocked.
- Async mid-run session recovery signs in on the current page
  (`_sign_in_on_current_page()`) like the sync path, instead of navigating away
  to `q=Python` first.
- `__version__` now matches `pyproject.toml` (was left at 0.2.11).

## [0.2.12] - 2026-07-14

### Added
- **Identifier-page fallback in auto sign-in** — when Google shows the email
  ("identifier") page instead of the account chooser (the profile lost its
  remembered account, e.g. after a server-side session revocation), the sign-in
  flow now enters the account email and continues to the password step. New
  `email` parameter on `auto_google_sign_in()` / `auto_google_sign_in_async()`
  and `google_email` field in `BrowserConfig`. Without an email that state was
  unrecoverable ("Could not select account from the list" forever).

### Fixed
- **`import_profile()` now replaces the destination instead of merging over
  it.** Previously `extractall` left stale files from the prior session in
  place — in particular sqlite `-wal`/`-shm` journals, which the next browser
  start replays OVER the freshly imported `cookies.sqlite`, silently undoing
  the import. Also, the destination directory name no longer has to match the
  tar's internal root directory name.

## [0.2.11] - 2026-05-31

### Added
- **`firefox_user_prefs` in `BrowserConfig`** — pass custom Firefox preferences
  to Camoufox (e.g. to disable GPU/hardware acceleration in Docker/CI).
  `BrowserConfig.DOCKER_GPU_PREFS` class constant provided as a ready-made
  preset: `BrowserConfig(firefox_user_prefs=BrowserConfig.DOCKER_GPU_PREFS)`.
  Applied in both sync (`TrendReq`) and async (`AsyncTrendReq`) browser init.

## [0.2.10] - 2026-05-22
### Added
- **`trending_analysis_merged()`** — convenience method that returns both topics
  and queries from a single browser navigation, avoiding duplicate page loads
  when you need both. Returns `{'topics': {...}, 'queries': {...}}`.

### Fixed
- **JSONP prefix parsing in `_handle_network_response`** — the browser network
  interceptor was not stripping the `)]}',` prefix (with comma) before JSON parsing,
  causing all `relatedsearches` API responses to silently fail. Added the comma
  variants `b")]}',\n"` (6 bytes) and `b")]}',"` (5 bytes) to the prefix removal
  logic in both sync and async handlers. This also fixes `related_topics()` and
  `related_queries()` in browser mode when the API returns the comma-prefixed format.

## [0.2.9] - 2026-05-22

### Added
- **Trending Analysis** — new browser-mode methods `trending_analysis_topics()` and
  `trending_analysis_queries()` that navigate to the Google Trends Explore page
  *without* a query keyword and capture the trending topics/queries for any
  combination of timeframe, geo, language, and Google property.
  - `timeframe` parameter: `'now 7-d'`, `'today 1-m'`, `'today 12-m'`, etc.
  - `geo` parameter: `'RU'`, `'KZ'`, `'US'`, etc. (empty = worldwide)
  - `hl` parameter: `'en'`, `'ru'`, etc.
  - `gprop` parameter: `''` (web), `'youtube'`, `'news'`, etc.
  - Both sync (`TrendReq`) and async (`AsyncTrendReq`) versions.

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
