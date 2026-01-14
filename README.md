# pytrends-modern

**The Modern Google Trends API** - Combining the best features from pytrends, trendspyg, and more.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Why pytrends-modern?

pytrends-modern is a **next-generation** Google Trends library that combines:

- ✅ **All classic pytrends features** - Interest over time, by region, related topics/queries
- ✅ **RSS Feed Support** - Fast real-time trending data with rich media (0.2s vs 10s)
- ✅ **Enhanced Error Handling** - Automatic retries, rate limit management, proxy rotation
- ✅ **Modern Python** - Full type hints, async support, dataclasses
- ✅ **Selenium Integration** - Advanced scraping when needed
- ✅ **Multiple Export Formats** - CSV, JSON, Parquet, Excel, DataFrame
- ✅ **Comprehensive CLI** - Easy command-line interface with rich output
- ✅ **Better Rate Limiting** - Smart backoff, quota management
- ✅ **Active Maintenance** - Modern codebase, actively maintained

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install pytrends-modern

# With browser mode (Camoufox for bypassing rate limits)
pip install pytrends-modern[browser]

# With Selenium support (for advanced scraping)
pip install pytrends-modern[selenium]

# With CLI support
pip install pytrends-modern[cli]

# With all features
pip install pytrends-modern[all]
```

### Basic Usage

```python
from pytrends_modern import TrendReq

# Initialize
pytrends = TrendReq(hl='en-US', tz=360)

# Build payload
pytrends.build_payload(
    kw_list=['Python', 'JavaScript'],
    timeframe='today 12-m',
    geo='US'
)

# Get interest over time
interest_df = pytrends.interest_over_time()
print(interest_df.head())

# Get interest by region
region_df = pytrends.interest_by_region()
print(region_df.head())

# Get related queries
related = pytrends.related_queries()
print(related['Python']['top'])
```

### 🦊 Browser Mode (Camoufox) - Bypass Rate Limits

**NEW!** Use Camoufox with advanced fingerprinting to bypass Google's rate limits by using your Google account:

```python
from pytrends_modern import TrendReq, BrowserConfig
from pytrends_modern.camoufox_setup import setup_profile

# First-time setup: Configure Google account login
setup_profile()  # Opens browser - log in to Google once

# Use browser mode (persistent login, no rate limits!)
config = BrowserConfig(headless=False)
pytrends = TrendReq(browser_config=config)

# Works like normal API
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
print(df.head())
```

**Avoiding 429 Rate Limits:**

If you're getting 429 errors even with browser mode, use these anti-rate-limit features:

```python
import random
from pytrends_modern import TrendReq, BrowserConfig

# Add delays + rotate OS fingerprint
os_choice = random.choice(['windows', 'macos', 'linux'])
config = BrowserConfig(
    headless=False,
    min_delay=3.0,             # Min delay between requests (seconds)
    max_delay=7.0,             # Max delay between requests
    persistent_context=True,    # Keep Google login
    os=os_choice,              # Rotate OS fingerprint
    humanize=True
)

pytrends = TrendReq(browser_config=config)
# Delays are automatically added before each request
```

**Anti-Rate-Limit Options:**
- `min_delay` / `max_delay` - Random delay between requests (default: 2-5s)
- `os` - Rotate between 'windows', 'macos', 'linux' for different fingerprints
- `persistent_context=False` - Fresh profile each time (no cookies)
- `proxy_server` - Use proxy to rotate IPs
- `humanize=True` - Human-like cursor movements (enabled by default)

**Browser Mode Limitations:**
- ⚠️ Only 1 keyword at a time (no comparisons)
- ⚠️ Only 'today 1-m' timeframe
- ⚠️ Only WORLDWIDE region
- ✅ No rate limits (uses your Google account)
- ✅ Perfect anti-detection with Camoufox fingerprinting

**Setup from command line:**
```bash
# Check profile status
python -m pytrends_modern.camoufox_setup status

# Run setup (opens browser for Google login)
python -m pytrends_modern.camoufox_setup

# Export profile for Docker/other machines
python -m pytrends_modern.camoufox_setup export camoufox-profile.tar.gz

# Import profile on another machine
python -m pytrends_modern.camoufox_setup import camoufox-profile.tar.gz
```

**Docker Usage:**

Yes! You can export your profile and use it in Docker containers:

```bash
# 1. Export profile locally
python -m pytrends_modern.camoufox_setup export profile.tar.gz

# 2. Use in Dockerfile
COPY profile.tar.gz /tmp/
RUN mkdir -p /root/.config && \
    cd /root/.config && \
    tar -xzf /tmp/profile.tar.gz

# 3. Use headless="virtual" in container
config = BrowserConfig(headless="virtual")  # Use Xvfb for Docker
```

**Headless Options:**
- `headless=False` - Show browser window (local development)
- `headless=True` - Standard headless (servers with display)
- `headless="virtual"` - Xvfb virtual display (Docker containers)

See `Dockerfile.example` and `examples/example_docker_usage.py` for complete Docker setup.

⚠️ **Security**: Profile contains Google session - keep secure, don't commit to git!

### RSS Feed (Fast Real-Time Data)

```python
from pytrends_modern import TrendsRSS

# Get trending searches with rich media
rss = TrendsRSS()
trends = rss.get_trends(geo='US')

for trend in trends:
    print(f"Title: {trend['title']}")
    print(f"Traffic: {trend['traffic']}")
    print(f"Articles: {len(trend['articles'])}")
    print(f"Image: {trend['picture']}")
    print("---")
```

### CLI Usage

```bash
# Get interest over time
pytrends-modern interest --keywords "Python,JavaScript" --timeframe "today 12-m"

# Get trending searches
pytrends-modern trending --geo US

# Get RSS feed
pytrends-modern rss --geo US --format json

# Export to CSV
pytrends-modern interest --keywords "AI" --output trends.csv
```

## 📊 Features Comparison

| Feature | pytrends | trendspyg | pytrends-modern |
|---------|----------|-----------|---------------|
| Interest Over Time | ✅ | ❌ | ✅ |
| Interest by Region | ✅ | ❌ | ✅ |
| Related Topics/Queries | ✅ | ❌ | ✅ |
| RSS Feed | ❌ | ✅ | ✅ |
| Rich Media (Images/Articles) | ❌ | ✅ | ✅ |
| Selenium Support | ❌ | ✅ | ✅ |
| Type Hints | ❌ | ✅ | ✅ |
| Async Support | ❌ | ❌ | ✅ |
| CLI | ❌ | ✅ | ✅ |
| Active Maintenance | ❌ | ✅ | ✅ |
| Auto Retry | Partial | ✅ | ✅ |
| Multiple Export Formats | ❌ | ✅ | ✅ |

## 🎯 Key Features

### 1. Classic Trends Data
All the beloved pytrends methods, modernized:
- `interest_over_time()` - Historical search interest
- `interest_by_region()` - Geographic distribution
- `related_topics()` - Related topics
- `related_queries()` - Related searches
- `trending_searches()` - Current trending searches
- `today_searches()` - Daily trends
- `realtime_trending_searches()` - Real-time trends
- `suggestions()` - Keyword suggestions

### 2. RSS Feed Support
Fast access to real-time trending data:
- **0.2 seconds** vs 10+ seconds for full scraping
- Rich media: images, news articles, headlines
- Perfect for monitoring and journalism
- Multiple geo support (125+ countries)

### 3. Enhanced Error Handling
- Automatic retry with exponential backoff
- Rate limit detection and management
- Proxy rotation support
- Better error messages

### 4. Modern Python Features
- Full type hints for IDE support
- Async/await support for concurrent requests
- Dataclasses for structured data
- Modern exception handling

### 5. Selenium Integration
- Fallback for advanced scraping needs
- Handles JavaScript-rendered content
- Automatic driver management
- Headless mode support

### 6. Multiple Export Formats
```python
# Export to various formats
df = pytrends.interest_over_time()

# CSV
df.to_csv('trends.csv')

# JSON
pytrends.to_json('trends.json')

# Parquet (requires pyarrow)
pytrends.to_parquet('trends.parquet')

# Excel (requires openpyxl)
df.to_excel('trends.xlsx')
```

## 📚 Documentation

### TrendReq Class

The main class for Google Trends API access.

```python
TrendReq(
    hl='en-US',          # Language
    tz=360,              # Timezone offset
    geo='',              # Geographic location
    timeout=(2, 5),      # (connect, read) timeouts
    proxies=None,        # Proxy list or dict
    retries=3,           # Number of retries
    backoff_factor=0.3,  # Backoff multiplier
    verify_ssl=True      # SSL verification
)
```

### Build Payload

```python
pytrends.build_payload(
    kw_list=['keyword1', 'keyword2'],  # Max 5 keywords
    cat=0,                              # Category (0 = all)
    timeframe='today 5-y',             # Time range
    geo='',                            # Geographic location
    gprop=''                           # Property ('', 'images', 'news', 'youtube', 'froogle')
)
```

### Time Frames
- `'now 1-H'` - Last hour
- `'now 4-H'` - Last 4 hours
- `'now 1-d'` - Last day
- `'now 7-d'` - Last 7 days
- `'today 1-m'` - Past 30 days
- `'today 3-m'` - Past 90 days
- `'today 12-m'` - Past 12 months
- `'today 5-y'` - Past 5 years (default)
- `'all'` - Since 2004
- `'YYYY-MM-DD YYYY-MM-DD'` - Custom range

### Geographic Codes
Use ISO 3166-1 alpha-2 country codes:
- `'US'` - United States
- `'GB'` - United Kingdom
- `'US-CA'` - California (US states)
- `'FR'` - France
- etc.

### Categories
Common category codes:
- `0` - All categories
- `3` - Arts & Entertainment
- `7` - Business & Industrial
- `16` - News
- `20` - Sports
- `32` - Science
- More at: https://github.com/pat310/google-trends-api/wiki/Google-Trends-Categories

## 🔧 Advanced Usage

### Proxy Support

```python
# List of proxies
pytrends = TrendReq(
    proxies=['https://proxy1.com:8080', 'https://proxy2.com:8080'],
    retries=3
)

# Dict format
pytrends = TrendReq(
    proxies={
        'http': 'http://proxy.com:8080',
        'https': 'https://proxy.com:8080'
    }
)
```

### Async Support

```python
import asyncio
from pytrends_modern import AsyncTrendReq

async def get_trends():
    pytrends = AsyncTrendReq(hl='en-US')
    await pytrends.build_payload(['Python', 'JavaScript'])
    df = await pytrends.interest_over_time()
    return df

df = asyncio.run(get_trends())
```

### Rate Limit Handling

```python
from pytrends_modern import TrendReq
from pytrends_modern.exceptions import TooManyRequestsError

pytrends = TrendReq(retries=5, backoff_factor=0.5)

try:
    pytrends.build_payload(['keyword'])
    df = pytrends.interest_over_time()
except TooManyRequestsError:
    print("Rate limited. Wait before retrying.")
```

### Batch Processing

```python
from pytrends_modern import TrendReq
import time

keywords = ['Python', 'JavaScript', 'Rust', 'Go', 'Java']
pytrends = TrendReq()

results = {}
for kw in keywords:
    pytrends.build_payload([kw], timeframe='today 12-m')
    results[kw] = pytrends.interest_over_time()
    time.sleep(2)  # Avoid rate limits
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=pytrends_modern

# Specific test
pytest tests/test_request.py::test_interest_over_time
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Credits

This project builds upon and combines features from:
- [pytrends](https://github.com/GeneralMills/pytrends) - Original Google Trends API
- [trendspyg](https://github.com/flack0x/trendspyg) - RSS feed support and modern features
- [google-trends Flask app](https://github.com/flack0x/google-trends) - Visualization and retry logic

## 📊 Changelog

### Version 1.0.0 (2025-12-26)
- Initial release
- Combined pytrends, trendspyg, and google-trends features
- Added async support
- Full type hints
- Enhanced error handling
- CLI interface
- Multiple export formats

## 📌 Important Notes

### Google API Changes

Google has deprecated several trending search API endpoints. **pytrends-modern provides two working alternatives:**

#### Option 1: Fast RSS Feed (Recommended for most use cases)
```python
from pytrends_modern import TrendsRSS

rss = TrendsRSS()
trends = rss.get_trends(geo='US')  # ~0.7s, returns 10 trends with images/articles
```
**Pros:** Lightning fast, includes rich media, no browser needed  
**Cons:** Limited to 10 trends, no filtering options

#### Option 2: Selenium Web Scraper (For complete data)
```python
from pytrends_modern import TrendsScraper

scraper = TrendsScraper(headless=True)
df = scraper.trending_searches(geo='US', hours=24)  # ~15s, returns 400+ trends
scraper.close()
```
**Pros:** Complete data (400+ trends), supports categories/filters  
**Cons:** Slower, requires Chrome browser

### Working Features
✅ All core API methods work perfectly:
- `interest_over_time()` - Historical search trends
- `interest_by_region()` - Geographic distribution  
- `related_queries()` / `related_topics()` - Related searches
- `suggestions()` - Keyword suggestions
- And more!

✅ RSS feeds for 125+ countries  
✅ Selenium scraper for comprehensive trending data

## ⚠️ Disclaimer

This is an unofficial library and is not affiliated with or endorsed by Google. Use responsibly and in accordance with Google's Terms of Service.
