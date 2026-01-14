#!/usr/bin/env python3
"""
Example: Using pytrends-modern with Camoufox browser mode

This example shows how to bypass Google's rate limits by using
your Google account with Camoufox's advanced fingerprinting.
"""

# Step 1: First-time setup (only need to do this once)
print("=" * 70)
print("STEP 1: Check if profile is configured")
print("=" * 70)

from pytrends_modern.camoufox_setup import is_profile_configured, setup_profile

if not is_profile_configured():
    print("\n⚠️  Profile not configured. Running setup...")
    print("This will open a browser for you to log in to Google.")
    print()
    
    # Run setup - browser will open
    setup_profile()
else:
    print("\n✅ Profile already configured!")
    print("Your Google login is saved and ready to use.\n")

# Step 2: Use browser mode
print("=" * 70)
print("STEP 2: Use browser mode with your Google account")
print("=" * 70)

from pytrends_modern import TrendReq, BrowserConfig

# Create browser configuration
config = BrowserConfig(
    headless=False,  # Set to True for headless mode
    humanize=True,   # Human-like cursor movements
    os='windows',      # or 'windows', 'macos'
    geoip=False       # Auto-detect location from IP
)

# Initialize with browser mode
pytrends = TrendReq(browser_config=config)

# Test with a keyword
keyword = "Brainrot"
print(f"\n🔍 Fetching data for: {keyword}")
print("⏳ Browser will open briefly...")

# Set keyword (browser mode only supports 1 keyword)
pytrends.kw_list = [keyword]

# Get interest over time
print("\n📊 Interest Over Time:")
df_time = pytrends.interest_over_time()
print(df_time.head(10))
print(f"Total: {len(df_time)} data points")

# Get interest by region
print("\n🌍 Interest By Region (Top 10):")
df_region = pytrends.interest_by_region()
df_region_sorted = df_region.sort_values(by=keyword, ascending=False).head(10)
print(df_region_sorted)

# Get related topics
print("\n🔗 Related Topics:")
topics = pytrends.related_topics()
if keyword in topics and topics[keyword].get('top') is not None:
    print(topics[keyword]['top'].head(10))
else:
    print("No related topics available")

# Get related queries
print("\n❓ Related Queries:")
queries = pytrends.related_queries()
if keyword in queries and queries[keyword].get('top') is not None:
    print(queries[keyword]['top'].head(10))
else:
    print("No related queries available")

print("\n" + "=" * 70)
print("✅ Example complete!")
print("=" * 70)
print("\n💡 Tips:")
print("   - Your Google login is saved in ~/.config/camoufox-pytrends-profile")
print("   - You only need to log in once")
print("   - Browser mode has NO rate limits!")
print("   - Camoufox's fingerprinting bypasses bot detection")
print("\n⚠️  Limitations:")
print("   - Only 1 keyword (no comparisons)")
print("   - Only 'today 1-m' timeframe")
print("   - Only WORLDWIDE region")
