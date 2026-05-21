#!/usr/bin/env python3
"""
Example: Trending Analysis — Google Trends Explore page without a query keyword

Discovers trending topics and queries for any region, language, and Google property
using Camoufox browser mode. No keyword needed — this is global analysis of what's
popular on YouTube, Google Search, etc.

Requires: pip install pytrends-modern[browser]
"""

from pytrends_modern import TrendReq, BrowserConfig

config = BrowserConfig(headless=False)
pytrends = TrendReq(browser_config=config)

# --- trending_analysis_merged: topics + queries in one navigation ---
print("=" * 70)
print("YouTube Trending in Russia (past 7 days)")
print("=" * 70)

result = pytrends.trending_analysis_merged(
    timeframe="now 7-d",
    geo="RU",
    hl="ru",
    gprop="youtube",
)

print("\nTop trending topics:")
if result["topics"]["top"] is not None:
    print(result["topics"]["top"][["topic_title", "topic_type", "value"]].head(10))
else:
    print("  No data")

print("\nRising topics:")
if result["topics"]["rising"] is not None:
    print(result["topics"]["rising"][["topic_title", "topic_type", "value"]].head(10))
else:
    print("  No data")

print("\nTop trending queries:")
if result["queries"]["top"] is not None:
    print(result["queries"]["top"][["query", "value"]].head(10))
else:
    print("  No data")

print("\nRising queries:")
if result["queries"]["rising"] is not None:
    print(result["queries"]["rising"][["query", "value"]].head(10))
else:
    print("  No data")

# --- Google Search trending in Kazakhstan (past month) ---
print("\n" + "=" * 70)
print("Google Search Trending in Kazakhstan (past month)")
print("=" * 70)

result_kz = pytrends.trending_analysis_merged(
    timeframe="today 1-m",
    geo="KZ",
    hl="en",
    gprop="",
)

print("\nTop trending topics:")
if result_kz["topics"]["top"] is not None:
    print(result_kz["topics"]["top"][["topic_title", "topic_type", "value"]].head(10))

print("\nTop trending queries:")
if result_kz["queries"]["top"] is not None:
    print(result_kz["queries"]["top"][["query", "value"]].head(10))

# --- Worldwide YouTube trending (past 12 months) ---
print("\n" + "=" * 70)
print("YouTube Trending Worldwide (past 12 months)")
print("=" * 70)

result_ww = pytrends.trending_analysis_merged(
    timeframe="today 12-m",
    geo="",
    hl="en",
    gprop="youtube",
)

print("\nTop trending topics:")
if result_ww["topics"]["top"] is not None:
    print(result_ww["topics"]["top"][["topic_title", "topic_type", "value"]].head(10))

print("\nTop trending queries:")
if result_ww["queries"]["top"] is not None:
    print(result_ww["queries"]["top"][["query", "value"]].head(10))

# --- Individual methods ---
print("\n" + "=" * 70)
print("Individual methods (same params, separate calls)")
print("=" * 70)

topics_only = pytrends.trending_analysis_topics(
    timeframe="now 7-d", geo="RU", hl="ru", gprop="youtube"
)
print("\nTopics only (top 5):")
if topics_only["top"] is not None:
    print(topics_only["top"][["topic_title", "value"]].head(5))

queries_only = pytrends.trending_analysis_queries(
    timeframe="now 7-d", geo="RU", hl="ru", gprop="youtube"
)
print("\nQueries only (top 5):")
if queries_only["top"] is not None:
    print(queries_only["top"][["query", "value"]].head(5))

print("\n" + "=" * 70)
print("Done!")
print("=" * 70)
print("\nParameters:")
print("  timeframe: 'now 1-H', 'now 4-H', 'now 1-d', 'now 7-d',")
print("             'today 1-m', 'today 3-m', 'today 12-m'")
print("  geo:       'RU', 'KZ', 'US', 'GB', etc. (empty = worldwide)")
print("  hl:        'en', 'ru', 'de', 'fr', etc.")
print("  gprop:     '' (web), 'youtube', 'news', 'images', 'froogle'")
