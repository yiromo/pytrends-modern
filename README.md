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

# With Selenium support (for advanced scraping)
pip install pytrends-modern[selenium]

# With CLI support
pip install pytrends-modern[cli]

# With all features
pip install pytrends-modern[all]
```

### Basic Usage

```python
from pytrends_plus import TrendReq

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

### RSS Feed (Fast Real-Time Data)

```python
from pytrends_plus import TrendsRSS

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
from pytrends_plus import AsyncTrendReq

async def get_trends():
    pytrends = AsyncTrendReq(hl='en-US')
    await pytrends.build_payload(['Python', 'JavaScript'])
    df = await pytrends.interest_over_time()
    return df

df = asyncio.run(get_trends())
```

### Rate Limit Handling

```python
from pytrends_plus import TrendReq
from pytrends_plus.exceptions import TooManyRequestsError

pytrends = TrendReq(retries=5, backoff_factor=0.5)

try:
    pytrends.build_payload(['keyword'])
    df = pytrends.interest_over_time()
except TooManyRequestsError:
    print("Rate limited. Wait before retrying.")
```

### Batch Processing

```python
from pytrends_plus import TrendReq
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
pytest --cov=pytrends_plus

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

## ⚠️ Disclaimer

This is an unofficial library and is not affiliated with or endorsed by Google. Use responsibly and in accordance with Google's Terms of Service.
