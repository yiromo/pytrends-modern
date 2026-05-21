# pytrends-modern

Modern Google Trends API — HTTP API, RSS feeds, browser automation, and Selenium scraping in one library.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Full Google Trends API** — interest over time, by region, related topics/queries, suggestions
- **RSS Feed** — fast real-time trending data with images and news articles
- **Camoufox Browser Mode** — bypass rate limits with anti-detection fingerprinting and Google account login
- **Auto Google Sign-In** — automated login flow, zero manual interaction
- **Async Support** — `AsyncTrendReq` with async Camoufox browser
- **Selenium Scraper** — CSV export for comprehensive trending data when API endpoints are deprecated
- **CLI** — command-line interface with Rich table output
- **Retry & Proxy Rotation** — exponential backoff, multi-proxy support, user-agent rotation

## Installation

```bash
pip install pytrends-modern

# Optional extras
pip install pytrends-modern[browser]    # Camoufox browser mode
pip install pytrends-modern[selenium]   # Selenium scraper
pip install pytrends-modern[cli]        # CLI with Rich output
pip install pytrends-modern[all]        # selenium + cli + export
```

## Quick Start

### HTTP API (Standard Mode)

```python
from pytrends_modern import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
pytrends.build_payload(
    kw_list=['Python', 'JavaScript'],
    timeframe='today 12-m',
    geo='US',
)

interest_df = pytrends.interest_over_time()
region_df = pytrends.interest_by_region()
related = pytrends.related_queries()
```

### RSS Feed

```python
from pytrends_modern import TrendsRSS

rss = TrendsRSS()
trends = rss.get_trends(geo='US')

for trend in trends:
    print(f"{trend['title']}: {trend['traffic']} traffic")
    for article in trend.get('articles', []):
        print(f"  - {article['title']} ({article['source']})")
```

### Browser Mode (Camoufox)

Uses a real browser with anti-detection fingerprinting to access Google Trends via your Google account. Requires a one-time profile setup.

```python
from pytrends_modern import TrendReq, BrowserConfig
from pytrends_modern.camoufox_setup import setup_profile

# One-time: open browser and log in to Google (saves profile)
setup_profile()

# After setup: use browser mode normally
config = BrowserConfig(headless=False)
pytrends = TrendReq(browser_config=config)
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
```

**Limitations:** 1 keyword per request, worldwide geo only, `today 1-m` or `today 12-m` timeframes.

> **Note:** Browser mode automatically uses the legacy Google Trends UI (`&legacy` parameter) for more reliable API responses and consistent behavior.

> **SVG Fallback:** When Google returns 429/500 errors and the API network responses are empty, `interest_over_time()` automatically falls back to scraping the SVG chart rendered in the browser. This extracts approximate values (0–100) from the chart's path coordinates, so data may be slightly less precise than the API response but still usable.

### Trending Analysis (Browser Mode)

Get trending topics and queries for any region, language, and Google property — **without specifying a keyword**. Navigates to the Explore page and captures the analysis data.

```python
from pytrends_modern import TrendReq, BrowserConfig

config = BrowserConfig(headless=False)
pytrends = TrendReq(browser_config=config)

# YouTube trending topics in Russia (past 7 days)
topics = pytrends.trending_analysis_topics(
    timeframe='now 7-d', geo='RU', hl='ru', gprop='youtube'
)
print(topics['top'].head())

# YouTube trending queries worldwide (past month)
queries = pytrends.trending_analysis_queries(
    timeframe='today 1-m', gprop='youtube'
)
print(queries['top'].head())

# Google Search trending topics in Kazakhstan
topics_kz = pytrends.trending_analysis_topics(
    timeframe='today 1-m', geo='KZ', hl='en'
)
```

**Parameters:** `timeframe` (e.g. `'now 7-d'`, `'today 1-m'`), `geo` (e.g. `'RU'`, `'KZ'`, empty=worldwide), `hl` (e.g. `'en'`, `'ru'`), `gprop` (e.g. `''`, `'youtube'`, `'news'`).

### Auto Google Sign-In

Automate the entire login flow — no manual interaction needed. Password is read from `BrowserConfig(google_password=...)` or the `GOOGLE_ACC_PASSWORD` environment variable.

```python
from pytrends_modern import TrendReq, BrowserConfig

config = BrowserConfig(
    google_sign_in=True,
    # google_password="...",           # or set GOOGLE_ACC_PASSWORD env var
)
pytrends = TrendReq(browser_config=config)  # auto sign-in on first use
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
```

Or run from the command line:

```bash
GOOGLE_ACC_PASSWORD="your_password" python -m pytrends_modern.camoufox_setup auto-signin
```

Auto sign-in also works if your session expires mid-run — it will detect the "Sign in" button and re-authenticate automatically.

### Selenium Scraper

For comprehensive trending data (400+ results) when the API is unavailable:

```python
from pytrends_modern import TrendsScraper

scraper = TrendsScraper(headless=True)
df = scraper.trending_searches(geo='US', hours=24)
scraper.close()
```

### CLI

```bash
pytrends-modern interest -k "Python,JavaScript" -t "today 12-m"
pytrends-modern region -k "Python" -g "US"
pytrends-modern rss -g US --format json -o trends.json
pytrends-modern suggest -k "python"
pytrends-modern trending -c united_states
```

## API Reference

### TrendReq

```python
TrendReq(
    hl='en-US',              # Language
    tz=360,                  # Timezone offset in minutes
    geo='',                  # Geographic location (e.g., 'US', 'US-CA')
    timeout=(10, 25),        # (connect, read) timeouts
    proxies=None,            # List[str] or Dict[str, str]
    retries=3,               # Retry attempts
    backoff_factor=0.3,      # Exponential backoff multiplier
    rotate_user_agent=True,  # Rotate user agents
    browser_config=None,     # BrowserConfig for Camoufox mode
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `build_payload(kw_list, cat, timeframe, geo, gprop)` | Set up query (max 5 keywords) |
| `interest_over_time()` | Historical search interest DataFrame |
| `interest_by_region(resolution, inc_low_vol, inc_geo_code)` | Geographic distribution |
| `related_topics()` | Related topics dict |
| `related_queries()` | Related queries dict |
| `trending_searches(pn)` | Trending searches by country |
| `today_searches(pn)` | Daily trends |
| `realtime_trending_searches(pn, cat, count)` | Real-time trends |
| `top_charts(date, hl, tz, geo)` | Top charts for a year |
| `suggestions(keyword)` | Keyword autocomplete suggestions |
| `categories()` | Available category list |

**Timeframes:** `now 1-H`, `now 4-H`, `now 1-d`, `now 7-d`, `today 1-m`, `today 3-m`, `today 12-m`, `today 5-y`, `all`, or `YYYY-MM-DD YYYY-MM-DD`.

### BrowserConfig

```python
from pytrends_modern import BrowserConfig

config = BrowserConfig(
    headless=False,           # bool or "virtual" (Xvfb for Docker)
    proxy_server=None,        # e.g., 'http://proxy.com:8080'
    proxy_username=None,
    proxy_password=None,
    user_data_dir=None,       # default: ~/.config/camoufox-pytrends-profile
    humanize=True,            # human-like cursor movement
    os='linux',               # fingerprint OS: 'windows', 'macos', 'linux'
    geoip=True,               # auto-detect geo from proxy IP
    min_delay=2.0,            # min delay between requests (seconds)
    max_delay=5.0,            # max delay between requests
    persistent_context=True,  # keep profile between sessions
    timeframe='today 1-m',    # 'today 1-m' or 'today 12-m'
    youtube=False,            # search YouTube instead of Google
    google_sign_in=False,     # auto sign-in if session expired
    google_password=None,     # or set GOOGLE_ACC_PASSWORD env var
)
```

### AsyncTrendReq

Async version of browser mode. Requires `BrowserConfig` (HTTP-only async is not supported).

```python
import asyncio
from pytrends_modern import AsyncTrendReq, BrowserConfig

async def main():
    config = BrowserConfig(headless=True)
    async with AsyncTrendReq(browser_config=config) as pytrends:
        pytrends.kw_list = ['Python']
        df = await pytrends.interest_over_time()
        print(df.head())

asyncio.run(main())
```

### TrendsRSS

```python
from pytrends_modern import TrendsRSS

rss = TrendsRSS(timeout=10)
trends = rss.get_trends(
    geo='US',                         # country or US state code
    output_format='dict',             # 'dict', 'json', 'csv', 'dataframe'
    include_images=True,
    include_articles=True,
    max_articles_per_trend=5,
)
```

### TrendsScraper

```python
from pytrends_modern import TrendsScraper

with TrendsScraper(headless=True) as scraper:
    df = scraper.trending_searches(geo='US', hours=24, category='all')
```

## Profile Management (CLI)

```bash
python -m pytrends_modern.camoufox_setup              # interactive setup
python -m pytrends_modern.camoufox_setup status        # check profile status
python -m pytrends_modern.camoufox_setup test          # test saved profile
python -m pytrends_modern.camoufox_setup clean         # clean cache/junk
python -m pytrends_modern.camoufox_setup export [path] # export for Docker
python -m pytrends_modern.camoufox_setup import_profile <path>  # import profile
python -m pytrends_modern.camoufox_setup auto-signin   # auto sign-in with password
```

## Proxy Support

```python
# List of proxies (automatic rotation)
pytrends = TrendReq(proxies=['https://proxy1:8080', 'https://proxy2:8080'])

# Dict format
pytrends = TrendReq(proxies={'https': 'https://proxy.com:8080'})

# Browser mode with proxy
config = BrowserConfig(proxy_server='http://proxy.com:8080', proxy_username='user', proxy_password='pass')
```

## Anti-Rate-Limiting (Browser Mode)

```python
import random
from pytrends_modern import TrendReq, BrowserConfig

config = BrowserConfig(
    headless=False,
    min_delay=3.0,
    max_delay=7.0,
    os=random.choice(['windows', 'macos', 'linux']),
    humanize=True,
    google_sign_in=True,  # auto re-login if session expires
)
pytrends = TrendReq(browser_config=config)
```

## Testing

```bash
pytest                                    # unit tests
pytest --integration                      # include live API tests
pytest --cov=pytrends_modern              # with coverage
```

## Credits

- [pytrends](https://github.com/GeneralMills/pytrends) — original Google Trends API
- [trendspyg](https://github.com/flack0x/trendspyg) — RSS feed support and Selenium approach

## Disclaimer

This is an unofficial library and is not affiliated with or endorsed by Google. Use responsibly and in accordance with Google's Terms of Service.
