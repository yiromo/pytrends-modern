#!/usr/bin/env python3
"""
Example: Using pytrends-modern in Docker containers

When running in Docker, use headless="virtual" to enable Xvfb virtual display.
This prevents display errors in containerized environments.
"""

import asyncio
from pytrends_modern import AsyncTrendReq, BrowserConfig


async def main():
    """Example async usage in Docker container"""
    
    # Configure for Docker environment
    config = BrowserConfig(
        headless="virtual",  # Use Xvfb virtual display for Docker
        humanize=True,
        os='linux',
        geoip=True
    )
    
    # For local development, use:
    # config = BrowserConfig(headless=False)  # Show browser window
    # config = BrowserConfig(headless=True)   # Standard headless
    
    print("🐳 Running pytrends-modern in Docker container...")
    print(f"📁 Profile: {config.user_data_dir}")
    
    async with AsyncTrendReq(browser_config=config) as pytrends:
        pytrends.kw_list = ["Docker"]
        
        # Get interest over time
        print("\n📊 Fetching interest_over_time...")
        df = await pytrends.interest_over_time()
        print(f"✓ Got {len(df)} rows")
        print(df.head())
        
        # Get interest by region
        print("\n🌍 Fetching interest_by_region...")
        df_region = await pytrends.interest_by_region()
        print(f"✓ Got {len(df_region)} rows")
        print(df_region.head())
    
    print("\n✅ Complete!")


if __name__ == "__main__":
    asyncio.run(main())
