#!/usr/bin/env python3
"""
Test AsyncTrendReq with Camoufox
"""

import asyncio
from pytrends_modern import AsyncTrendReq, BrowserConfig

async def test_async_browser_mode():
    """Test async browser mode with all 4 APIs"""
    print("=" * 70)
    print("Testing AsyncTrendReq with Camoufox")
    print("=" * 70)
    
    # Configure browser
    config = BrowserConfig(
        headless=False,
        humanize=True,
        os='linux',
        geoip=True
    )
    
    keyword = "Python"
    print(f"\n🔍 Testing with keyword: {keyword}")
    
    # Use async context manager
    async with AsyncTrendReq(browser_config=config) as pytrends:
        pytrends.kw_list = [keyword]
        
        # Test interest_over_time
        print("\n📊 Testing interest_over_time()...")
        try:
            df_iot = await pytrends.interest_over_time()
            print(f"✓ interest_over_time: {len(df_iot)} rows")
            print(df_iot.head())
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Test interest_by_region
        print("\n🌍 Testing interest_by_region()...")
        try:
            df_ibr = await pytrends.interest_by_region()
            print(f"✓ interest_by_region: {len(df_ibr)} rows")
            print(df_ibr.head())
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Test related_topics
        print("\n🔗 Testing related_topics()...")
        try:
            topics = await pytrends.related_topics()
            if keyword in topics and topics[keyword].get('top') is not None:
                print(f"✓ related_topics: {len(topics[keyword]['top'])} topics")
                print(topics[keyword]['top'].head())
            else:
                print("✓ related_topics: No data (might be normal)")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Test related_queries
        print("\n❓ Testing related_queries()...")
        try:
            queries = await pytrends.related_queries()
            if keyword in queries and queries[keyword].get('top') is not None:
                print(f"✓ related_queries: {len(queries[keyword]['top'])} queries")
                print(queries[keyword]['top'].head())
            else:
                print("✓ related_queries: No data (might be normal)")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Async test complete!")
    print("=" * 70)

if __name__ == "__main__":
    # Run async test
    asyncio.run(test_async_browser_mode())
