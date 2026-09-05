# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`pytrends-modern` — an unofficial Google Trends client packaged as `pytrends_modern/`. Published to PyPI; GitHub: yiromo/pytrends-modern.

## Commands

```bash
pip install -e ".[dev,all]"        # dev install (uv.lock also present: `uv sync` works)
playwright install firefox         # required for browser mode (Camoufox)

pytest                             # unit tests (addopts always adds --cov)
pytest --no-cov                    # skip coverage while iterating
pytest tests/test_basic.py::TestTrendReq::test_initialization   # single test
pytest --integration               # also run @pytest.mark.integration (live network); skipped by default via conftest hook

black pytrends_modern/             # line-length 100
ruff check pytrends_modern/
mypy pytrends_modern/ --ignore-missing-imports
```

CI (`.github/workflows/test.yaml`) runs pytest on Python 3.8–3.13 × ubuntu/windows/macos; the lint job is `continue-on-error`, so black/ruff/mypy failures do not block.

Browser-profile lifecycle (needed before any browser-mode work):

```bash
python -m pytrends_modern.camoufox_setup            # interactive Google login, saves profile
python -m pytrends_modern.camoufox_setup status|test|clean
python -m pytrends_modern.camoufox_setup export [path]   # tar.gz for Docker (see Dockerfile.example)
python -m pytrends_modern.camoufox_setup import_profile <path>
GOOGLE_ACC_PASSWORD=... python -m pytrends_modern.camoufox_setup auto-signin
```

Release: bump the version in **both** `pyproject.toml` and `pytrends_modern/__init__.py`, add a CHANGELOG entry, tag `vX.Y.Z`, `python -m build`, `twine upload dist/*`.

## Architecture

### `TrendReq` has two backends in one class

`TrendReq.__init__` sets `self.browser_mode = browser_config is not None`. Every public data method (`interest_over_time`, `interest_by_region`, `related_topics`, `related_queries`) branches on that flag at the top. The two paths share only the `_parse_*_response` helpers.

**HTTP path** (no `browser_config`): `build_payload()` builds `token_payload` and calls `_get_tokens()`, which POSTs `/api/explore` and splits the returned widgets into `interest_over_time_widget`, `interest_by_region_widget`, `related_topics_widget_list`, `related_queries_widget_list`. Each data method then GETs its widget endpoint with that widget's `token` + `request`, through `_get_data()` (session-level `Retry` on `ERROR_CODES`, proxy rotation, cookie from `_get_google_cookie()`).

**Browser path** (`BrowserConfig` passed): no tokens at all. `_capture_all_api_responses(keyword)` navigates once to `trends.google.com/trends/explore?...&legacy&hl=en-GB`, and a Playwright `page.on("response")` handler (`_handle_network_response`) intercepts every `/trends/api/widgetdata/` response and stores it in `self.browser_responses_cache` keyed by URL substring:

| URL fragment | cache key |
|---|---|
| `/widgetdata/multiline` | `interest_over_time` |
| `/widgetdata/comparedgeo` | `interest_by_region` |
| `/widgetdata/relatedsearches` + `keywordType":"ENTITY` | `related_topics` |
| `/widgetdata/relatedsearches` + `keywordType":"QUERY` | `related_queries` |

So **one navigation populates all four methods**; a method only navigates when its key is missing. The cache is cleared at the start of each capture. `trending_analysis_*()` use a separate capture (`_capture_analysis_responses`) that loads Explore with *no* `q=` and takes `timeframe`/`geo`/`hl`/`gprop` as method arguments rather than from `BrowserConfig`.

Browser mode is deliberately limited: 1 keyword, worldwide geo, timeframe from `BrowserConfig.timeframe`. `build_payload()` skips `_get_tokens()` in this mode, and setting `pytrends.kw_list = [...]` directly is the documented usage.

### Google's JSONP prefix — a repeat bug source

Responses start with `)]}'` in several variants (`)]}',\n`, `)]}',`, `)]}'\n`, `)]}'`). Both backends strip it with the single `utils.strip_jsonp_prefix()` helper (regex `^\)\]\}',?\s*`, str or bytes): the HTTP path in `_get_data()`, the browser path in `_handle_network_response` of `request.py` *and* `request_async.py`. A body the helper cannot turn into JSON fails **silently** in the browser handler (it swallows exceptions) and shows up as an empty cache — this was the 0.2.10 bug. Add new variants to the helper, not inline.

The browser cache is tagged with the navigation that filled it (`self._browser_cache_key`: `("explore", keyword)` or `("analysis", timeframe, geo, hl, gprop)`); data methods re-navigate when the tag does not match (`_browser_cache_valid`). Capture methods wait for the expected keys with `_wait_for_cached_keys()` (polling via `page.wait_for_timeout` — in sync Playwright, `time.sleep` blocks event dispatch, so response handlers never fire during a plain sleep).

### Fallbacks

When the cache stays empty after a re-navigation (Google returned 429/500), `interest_over_time()` falls back to `_scrape_interest_over_time_from_svg()`, which parses the rendered chart's SVG `<path d="M...">` coordinates into approximate 0–100 values. Other methods raise instead.

When `google_sign_in=True`, both capture methods check `_find_sign_in_button()` after navigation, run `auto_google_sign_in()`, clear the cache and re-navigate — so a mid-run session expiry is recovered transparently.

### `AsyncTrendReq` is a near-duplicate of the browser path

`request_async.py` re-implements the whole browser flow with `camoufox.async_api`, but reuses the sync parsers by calling the unbound methods with its own instance: `TrendReq._parse_multiline_response(self, data)`. That works only because both classes expose the same attribute names (`kw_list`, `browser_responses_cache`, `browser_config`, `browser_page`). **Any browser-mode change in `request.py` must be mirrored in `request_async.py`**, and any parser change must not start relying on HTTP-only attributes. It is browser-only — there is no HTTP async client.

`camoufox_setup.py` duplicates the same way: sync helpers (`_find_sign_in_button`, `_fill_password`, …) and `_a`-prefixed async twins (`_afind_sign_in_button`, …) driving `auto_google_sign_in()` / `auto_google_sign_in_async()`.

### Two `BrowserConfig` classes

`browser_config_camoufox.py` holds the real, exported `BrowserConfig` (Camoufox/Firefox). `browser_config.py` is a stale DrissionPage/Chromium config that nothing imports — edit the `_camoufox` one. Note `TrendReq.__init__`'s docstring still describes the DrissionPage version.

`BrowserConfig` fields are read via `getattr(..., default)` in most call sites, so adding a field rarely breaks callers — but it must be threaded through both `TrendReq._init_camoufox` and `AsyncTrendReq._init_camoufox` to take effect.

### Optional dependencies

Extras: `browser` (camoufox), `selenium` (Selenium scraper), `cli` (click+rich), `export` (pyarrow/openpyxl). Imports of these are guarded: `TrendsScraper` is set to `None` in `__init__.py` if selenium is missing, `cli.py` defines a stub `main()` when click is absent, and `_init_camoufox` raises a pip-install hint on ImportError. Keep new optional imports lazy (inside functions) so the base install stays `requests`/`pandas`/`lxml` only.

### Other modules

- `rss.py` — `TrendsRSS`, independent of `TrendReq`; parses `trends.google.com/trending/rss?geo=` with `xml.etree`, validates geo against `COUNTRIES`/`US_STATES` in `config.py`, and formats to dict/json/csv/dataframe.
- `scraper.py` — `TrendsScraper`, Selenium CSV-download path for trending searches; a separate approach used when the API endpoints are unavailable.
- `config.py` — all endpoint URLs, `ERROR_CODES`, `USER_AGENTS`, `COUNTRIES`, `US_STATES`, `VALID_GPROP`, `VALID_TIME_PERIODS`. Add new endpoints here, not inline.
- `exceptions.py` — everything derives from `PyTrendsPlusError`; `ResponseError.from_response()` / `TooManyRequestsError.from_response()` are the standard constructors for HTTP failures.

## Conventions

- Google-style docstrings with `Args:`/`Returns:`/`Raises:` and a `>>>` example on public methods; type hints everywhere (mypy config sets `disallow_untyped_defs`).
- `test_space/` is a scratch directory: gitignored, but declared as a `[tool.uv.workspace]` member, so it must exist for `uv sync` to resolve.
- `tests/` contains only offline unit tests using the fixtures in `conftest.py`; anything hitting the network gets `@pytest.mark.integration`.
