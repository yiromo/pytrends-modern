# pytrends-modern Examples

This directory contains usage examples for pytrends-modern.

## Files

- **basic_usage.py** - Basic examples covering common use cases
- **advanced_usage.py** - Advanced examples with custom features

## Running Examples

Make sure you have pytrends-modern installed:

```bash
pip install pytrends-modern

# Or with all optional dependencies
pip install pytrends-modern[all]
```

Then run any example:

```bash
python examples/basic_usage.py
python examples/advanced_usage.py
```

## Basic Usage Examples

### 1. Interest Over Time
Get historical search interest for keywords:
```python
from pytrends_plus import TrendReq

pytrends = TrendReq()
pytrends.build_payload(['Python', 'JavaScript'], timeframe='today 12-m')
df = pytrends.interest_over_time()
print(df.head())
```

### 2. Interest by Region
Get geographic distribution of searches:
```python
pytrends.build_payload(['Python'], geo='US')
df = pytrends.interest_by_region(resolution='REGION')
print(df.head())
```

### 3. RSS Feed (Fast!)
Get real-time trending searches in 0.2 seconds:
```python
from pytrends_plus import TrendsRSS

rss = TrendsRSS()
trends = rss.get_trends(geo='US')
for trend in trends[:5]:
    print(f"{trend['title']}: {trend['traffic']}")
```

## Advanced Usage Examples

### 1. Proxy and Retry Configuration
```python
pytrends = TrendReq(
    proxies=['https://proxy1.com:8080'],
    retries=3,
    backoff_factor=0.5
)
```

### 2. Custom Date Ranges
```python
from datetime import date, timedelta
from pytrends_plus.utils import convert_dates_to_timeframe

end_date = date.today()
start_date = end_date - timedelta(days=180)
timeframe = convert_dates_to_timeframe(start_date, end_date)

pytrends.build_payload(['AI'], timeframe=timeframe)
df = pytrends.interest_over_time()
```

### 3. Batch Processing
```python
keywords = ['Python', 'JavaScript', 'Java']
results = {}

for kw in keywords:
    pytrends.build_payload([kw], timeframe='today 12-m')
    df = pytrends.interest_over_time()
    results[kw] = df[kw].mean()
```

### 4. Trend Analysis
```python
from pytrends_plus.utils import calculate_trend_momentum, detect_trend_spikes

pytrends.build_payload(['ChatGPT'], timeframe='today 12-m')
df = pytrends.interest_over_time()

# Calculate momentum
momentum = calculate_trend_momentum(df, 'ChatGPT', window=7)

# Detect spikes
spikes = detect_trend_spikes(df, 'ChatGPT', threshold=2.0)
```

### 5. Export to Multiple Formats
```python
from pytrends_plus.utils import export_to_multiple_formats

paths = export_to_multiple_formats(
    df,
    'my_trends',
    formats=['csv', 'json', 'parquet']
)
```

## CLI Examples

### Get Interest Over Time
```bash
pytrends-modern interest -k "Python,JavaScript" -t "today 12-m"
```

### Get Interest by Region
```bash
pytrends-modern region -k "AI" -g "US" -r "REGION"
```

### Get RSS Trends
```bash
pytrends-modern rss -g US --format table
```

### Export to File
```bash
pytrends-modern interest -k "Python" -o trends.csv
pytrends-modern rss -g GB -o trends.json --format json
```

## Tips

1. **Rate Limiting**: Add delays between requests to avoid rate limits
   ```python
   import time
   time.sleep(1)  # Wait 1 second between requests
   ```

2. **Error Handling**: Always wrap API calls in try-except
   ```python
   try:
       df = pytrends.interest_over_time()
   except Exception as e:
       print(f"Error: {e}")
   ```

3. **RSS for Speed**: Use RSS feed for real-time monitoring (0.2s vs 10s)

4. **Data Validation**: Check if DataFrame is empty before processing
   ```python
   if not df.empty:
       # Process data
       pass
   ```

## More Help

- Check the [README](../README.md) for full documentation
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub for questions
