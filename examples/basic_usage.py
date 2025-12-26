"""
Basic usage examples for pytrends-modern
"""

from pytrends_modern import TrendReq, TrendsRSS

# Example 1: Basic Interest Over Time
print("=" * 60)
print("Example 1: Interest Over Time")
print("=" * 60)

pytrends = TrendReq(hl="en-US", tz=360)
pytrends.build_payload(["Python", "JavaScript"], timeframe="today 12-m")
df = pytrends.interest_over_time()

print(df.head())
print(f"\nData shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")

# Example 2: Interest by Region
print("\n" + "=" * 60)
print("Example 2: Interest by Region")
print("=" * 60)

pytrends.build_payload(["Python"], geo="US")
df_region = pytrends.interest_by_region(resolution="REGION")

print(df_region.head(10))
print(f"\nTop region: {df_region['Python'].idxmax()} with score {df_region['Python'].max()}")

# Example 3: Related Queries
print("\n" + "=" * 60)
print("Example 3: Related Queries")
print("=" * 60)

pytrends.build_payload(["Python"])
related = pytrends.related_queries()

print("Top related queries for 'Python':")
if related["Python"]["top"] is not None:
    print(related["Python"]["top"].head())
else:
    print("No top queries available")

print("\nRising related queries for 'Python':")
if related["Python"]["rising"] is not None:
    print(related["Python"]["rising"].head())
else:
    print("No rising queries available")

# Example 4: Trending Searches
print("\n" + "=" * 60)
print("Example 4: Trending Searches")
print("=" * 60)

try:
    df_trending = pytrends.trending_searches(pn="united_states")
    print("Current trending searches in the US:")
    print(df_trending.head(10))
except Exception as e:
    print(f"Error fetching trending searches: {e}")

# Example 5: RSS Feed (Fast!)
print("\n" + "=" * 60)
print("Example 5: RSS Feed - Fast Real-Time Trends")
print("=" * 60)

rss = TrendsRSS()
trends = rss.get_trends(geo="US", include_articles=True)

print(f"Found {len(trends)} trending topics")
print("\nTop 5 trends:")
for i, trend in enumerate(trends[:5], 1):
    print(f"\n{i}. {trend['title']}")
    print(f"   Traffic: {trend['traffic']}")
    print(f"   Articles: {trend.get('article_count', 0)}")
    if trend.get("articles"):
        print(f"   First article: {trend['articles'][0]['title'][:60]}...")

# Example 6: Keyword Suggestions
print("\n" + "=" * 60)
print("Example 6: Keyword Suggestions")
print("=" * 60)

suggestions = pytrends.suggestions("artificial intelligence")
print("Suggestions for 'artificial intelligence':")
for suggestion in suggestions[:5]:
    print(f"  - {suggestion['title']} ({suggestion.get('type', 'unknown')})")

# Example 7: Multiple Timeframes Comparison
print("\n" + "=" * 60)
print("Example 7: Compare Different Time Periods")
print("=" * 60)

# Last month
pytrends.build_payload(["AI"], timeframe="today 1-m")
df_1m = pytrends.interest_over_time()
avg_1m = df_1m["AI"].mean()

# Last year
pytrends.build_payload(["AI"], timeframe="today 12-m")
df_12m = pytrends.interest_over_time()
avg_12m = df_12m["AI"].mean()

print(f"Average interest for 'AI':")
print(f"  Last month: {avg_1m:.2f}")
print(f"  Last year: {avg_12m:.2f}")
print(f"  Change: {((avg_1m - avg_12m) / avg_12m * 100):.1f}%")

print("\n" + "=" * 60)
print("Examples completed!")
print("=" * 60)
