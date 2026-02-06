#!/usr/bin/env python3
"""
Example: Using different timeframes with browser mode

Test both 'today 1-m' (default) and 'today 12-m' (past 12 months)
"""

from pytrends_modern import TrendReq, BrowserConfig

keyword = "Python"

print("=" * 70)
print("Testing Different Timeframes")
print("=" * 70)

# Test 1: Default timeframe (today 1-m)
print("\n📊 Test 1: Default timeframe (past month)")
config1 = BrowserConfig(
    headless=False,
    min_delay=2.0,
    max_delay=4.0,
)
print(f"Timeframe: {config1.timeframe}")

pytrends1 = TrendReq(browser_config=config1)
pytrends1.kw_list = [keyword]
df1 = pytrends1.interest_over_time()
print(f"✓ Got {len(df1)} data points")
print(df1.head())
print(f"Date range: {df1.index.min()} to {df1.index.max()}")

# Close first browser before opening second
pytrends1._close_browser()
del pytrends1

# Test 2: Past 12 months
print("\n📊 Test 2: Past 12 months")
config2 = BrowserConfig(
    headless=False,
    min_delay=2.0,
    max_delay=4.0,
    timeframe='today 12-m'
)
print(f"Timeframe: {config2.timeframe}")

pytrends2 = TrendReq(browser_config=config2)
pytrends2.kw_list = [keyword]
df2 = pytrends2.interest_over_time()
print(f"✓ Got {len(df2)} data points")
print(df2.head())
print(f"Date range: {df2.index.min()} to {df2.index.max()}")

print("\n✅ Both timeframes working!")
print(f"\nPast month: {len(df1)} points")
print(f"Past 12 months: {len(df2)} points")
