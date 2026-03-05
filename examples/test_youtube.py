#!/usr/bin/env python3
"""Test YouTube search in browser mode"""

from pytrends_modern import TrendReq, BrowserConfig

keyword = "Murder Mystery 2"
print(f"Testing YouTube search for: '{keyword}'")

config = BrowserConfig(
    headless=False,
    youtube=True,
    timeframe='today 1-m',
    min_delay=2.0,
    max_delay=4.0,
)

print(f"  youtube={config.youtube}, timeframe={config.timeframe}")

pytrends = TrendReq(browser_config=config)
pytrends.kw_list = [keyword]

df = pytrends.interest_over_time()
print(f"\n✅ YouTube interest_over_time: {len(df)} rows")
print(df.head())
print(f"Date range: {df.index.min().date()} → {df.index.max().date()}")
