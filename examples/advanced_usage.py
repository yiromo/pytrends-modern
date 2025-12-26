"""
Advanced usage examples for pytrends-modern
"""

import time
from datetime import date, timedelta

from pytrends_modern import TrendReq, TrendsRSS
from pytrends_modern.utils import (
    convert_dates_to_timeframe,
    calculate_trend_momentum,
    detect_trend_spikes,
    export_to_multiple_formats,
)

# Example 1: Using Proxies and Retries
print("=" * 60)
print("Example 1: Using Proxies and Enhanced Error Handling")
print("=" * 60)

# Initialize with retry logic
pytrends = TrendReq(retries=3, backoff_factor=0.5, timeout=(10, 25))

try:
    pytrends.build_payload(["Python"], timeframe="today 12-m")
    df = pytrends.interest_over_time()
    print(f"Successfully fetched {len(df)} data points")
except Exception as e:
    print(f"Error: {e}")

# Example 2: Custom Date Range
print("\n" + "=" * 60)
print("Example 2: Custom Date Range")
print("=" * 60)

# Get trends for specific date range
end_date = date.today()
start_date = end_date - timedelta(days=180)
timeframe = convert_dates_to_timeframe(start_date, end_date)

print(f"Timeframe: {timeframe}")

pytrends.build_payload(["Machine Learning"], timeframe=timeframe)
df = pytrends.interest_over_time()
print(f"Data points: {len(df)}")
print(df.head())

# Example 3: Batch Processing Multiple Keywords
print("\n" + "=" * 60)
print("Example 3: Batch Processing Multiple Keywords")
print("=" * 60)

keywords = ["Python", "JavaScript", "Java", "C++", "Go"]
results = {}

for kw in keywords:
    try:
        pytrends.build_payload([kw], timeframe="today 12-m")
        df = pytrends.interest_over_time()
        results[kw] = df[kw].mean()
        print(f"{kw}: Average interest = {results[kw]:.2f}")
        time.sleep(1)  # Avoid rate limits
    except Exception as e:
        print(f"Error for {kw}: {e}")
        results[kw] = 0

# Sort by popularity
sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
print("\nLanguages ranked by interest:")
for i, (lang, score) in enumerate(sorted_results, 1):
    print(f"{i}. {lang}: {score:.2f}")

# Example 4: Trend Momentum Analysis
print("\n" + "=" * 60)
print("Example 4: Trend Momentum Analysis")
print("=" * 60)

pytrends.build_payload(["ChatGPT"], timeframe="today 12-m")
df = pytrends.interest_over_time()

momentum = calculate_trend_momentum(df, "ChatGPT", window=7)
print("Recent momentum (7-day rolling average % change):")
print(momentum.tail(10))

avg_momentum = momentum.mean()
print(f"\nAverage momentum: {avg_momentum:.2f}%")

# Example 5: Detect Trend Spikes
print("\n" + "=" * 60)
print("Example 5: Detect Significant Spikes")
print("=" * 60)

spikes = detect_trend_spikes(df, "ChatGPT", threshold=1.5)
print(f"Found {len(spikes)} significant spike periods:")
print(spikes[["ChatGPT"]].head())

# Example 6: Multi-Region Comparison
print("\n" + "=" * 60)
print("Example 6: Multi-Region Comparison")
print("=" * 60)

regions = ["US", "GB", "CA", "AU"]
region_data = {}

for region in regions:
    pytrends.build_payload(["AI"], geo=region, timeframe="today 1-m")
    df = pytrends.interest_over_time()
    region_data[region] = df["AI"].mean()
    print(f"{region}: {region_data[region]:.2f}")
    time.sleep(1)

# Example 7: Multiple RSS Feeds
print("\n" + "=" * 60)
print("Example 7: Multiple RSS Feeds")
print("=" * 60)

rss = TrendsRSS()
countries = ["US", "GB", "CA"]

all_trends = rss.get_trends_for_multiple_geos(
    geos=countries, output_format="dict", include_articles=False
)

for country, trends in all_trends.items():
    if trends:
        print(f"\n{country}: Top 3 trends")
        for i, trend in enumerate(trends[:3], 1):
            print(f"  {i}. {trend['title']}")

# Example 8: Export to Multiple Formats
print("\n" + "=" * 60)
print("Example 8: Export to Multiple Formats")
print("=" * 60)

pytrends.build_payload(["Python"], timeframe="today 12-m")
df = pytrends.interest_over_time()

# Export to multiple formats
try:
    paths = export_to_multiple_formats(df, "python_trends", formats=["csv", "json"])
    print("Exported files:")
    for fmt, path in paths.items():
        print(f"  {fmt}: {path}")
except Exception as e:
    print(f"Export error: {e}")

# Example 9: Related Topics Analysis
print("\n" + "=" * 60)
print("Example 9: Related Topics Deep Dive")
print("=" * 60)

pytrends.build_payload(["Machine Learning"])
topics = pytrends.related_topics()

if topics["Machine Learning"]["rising"] is not None:
    rising = topics["Machine Learning"]["rising"]
    print("Rising related topics:")
    print(rising.head(10))
else:
    print("No rising topics available")

# Example 10: Realtime Trending
print("\n" + "=" * 60)
print("Example 10: Realtime Trending Searches")
print("=" * 60)

try:
    realtime = pytrends.realtime_trending_searches(pn="US", count=10)
    print("Real-time trending:")
    print(realtime)
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Advanced examples completed!")
print("=" * 60)
