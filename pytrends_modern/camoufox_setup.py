"""
Camoufox setup and configuration helper for pytrends-modern

This module helps users set up their Google account login for browser mode.
"""

import os
from typing import Optional


def get_default_profile_dir() -> str:
    """Get the default Camoufox profile directory"""
    return os.path.expanduser('~/.config/camoufox-pytrends-profile')


def is_profile_configured(profile_dir: Optional[str] = None) -> bool:
    """
    Check if Camoufox profile is configured (has Google login)
    
    Args:
        profile_dir: Custom profile directory, or None for default
        
    Returns:
        True if profile exists and appears configured
    """
    if profile_dir is None:
        profile_dir = get_default_profile_dir()
    else:
        profile_dir = os.path.expanduser(profile_dir)
    
    # Check if profile directory exists and has content
    if not os.path.exists(profile_dir):
        return False
    
    # Check if it has Firefox profile structure (indicates browser has been used)
    # Camoufox uses Firefox, so we check for common Firefox profile files
    profile_indicators = [
        'prefs.js',
        'cookies.sqlite',
        'storage',
    ]
    
    for indicator in profile_indicators:
        if os.path.exists(os.path.join(profile_dir, indicator)):
            return True
    
    return False


def setup_profile(profile_dir: Optional[str] = None, headless: bool = False) -> bool:
    """
    Interactive setup: Open browser for user to log in to Google
    
    Args:
        profile_dir: Custom profile directory, or None for default
        headless: Run in headless mode (not recommended for first setup)
        
    Returns:
        True if setup completed successfully
        
    Raises:
        ImportError: If Camoufox is not installed
    """
    try:
        from camoufox.sync_api import Camoufox
    except ImportError:
        raise ImportError(
            "Camoufox is required for browser mode. "
            "Install with: pip install pytrends-modern[browser]"
        )
    
    if profile_dir is None:
        profile_dir = get_default_profile_dir()
    else:
        profile_dir = os.path.expanduser(profile_dir)
    
    print("=" * 70)
    print("🔧 Camoufox Profile Setup for pytrends-modern")
    print("=" * 70)
    print(f"\n📁 Profile directory: {profile_dir}")
    
    if is_profile_configured(profile_dir):
        print("✓ Profile already exists")
        response = input("\nReconfigure profile? This will open the browser again (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    print("\n📖 Instructions:")
    print("1. Browser will open to Google Trends")
    print("2. Log in to your Google account")
    print("3. Once logged in and page loads, press Enter here")
    print("4. Your login will be saved for future use")
    print("\n⚠️  IMPORTANT: Browser mode has limitations:")
    print("   - Only 1 keyword at a time (no comparisons)")
    print("   - Only 'today 1-m' timeframe")
    print("   - Only WORLDWIDE region")
    print()
    
    input("Press Enter to open browser...")
    
    try:
        with Camoufox(
            persistent_context=True,
            user_data_dir=profile_dir,
            headless=headless,
            humanize=True,
            os='linux',
            geoip=True,
        ) as context:
            page = context.pages[0] if context.pages else context.new_page()
            
            print("\n🌐 Opening Google Trends...")
            print("   Please log in to your Google account")
            
            # Navigate to Google Trends
            page.goto(
                "https://trends.google.com/trends/explore?q=Python&hl=en-GB",
                wait_until='networkidle',
                timeout=60000
            )
            
            title = page.title()
            if "429" in title or "error" in title.lower():
                print(f"\n⚠️  Page title: {title}")
                print("   You may need to log in or solve a CAPTCHA")
            else:
                print(f"✓ Page loaded: {title}")
            
            print("\n📋 Please:")
            print("   1. Log in to Google if not already logged in")
            print("   2. Make sure the page loads correctly")
            print("   3. Then come back here and press Enter")
            
            input("\nPress Enter when done (browser will close)...")
            
        # Verify profile was created
        if is_profile_configured(profile_dir):
            print("\n✅ SUCCESS! Profile configured successfully")
            print(f"📁 Profile saved to: {profile_dir}")
            print("\n💡 You can now use pytrends-modern with browser mode:")
            print("   from pytrends_modern import TrendReq, BrowserConfig")
            print("   config = BrowserConfig()")
            print("   pytrends = TrendReq(browser_config=config)")
            return True
        else:
            print("\n⚠️  Warning: Profile directory exists but may not be fully configured")
            print("   Try running setup again or check if browser saved data")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        return False


def test_profile(profile_dir: Optional[str] = None, headless: bool = False) -> bool:
    """
    Open the browser with the saved profile to verify it works.

    Args:
        profile_dir: Profile directory to test, or None for default
        headless: Run in headless mode

    Returns:
        True if browser opened successfully
    """
    try:
        from camoufox.sync_api import Camoufox
    except ImportError:
        raise ImportError(
            "Camoufox is required for browser mode. "
            "Install with: pip install pytrends-modern[browser]"
        )

    if profile_dir is None:
        profile_dir = get_default_profile_dir()
    else:
        profile_dir = os.path.expanduser(profile_dir)

    if not is_profile_configured(profile_dir):
        print(f"❌ No profile found at: {profile_dir}")
        print("   Run setup first: python -m pytrends_modern.camoufox_setup")
        return False

    print(f"🦊 Opening browser with profile: {profile_dir}")
    print("   Close the browser window when done.")

    try:
        with Camoufox(
            persistent_context=True,
            user_data_dir=profile_dir,
            headless=headless,
            humanize=True,
            geoip=False,
        ) as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://trends.google.com/", wait_until="domcontentloaded", timeout=30000)
            print(f"✅ Browser opened. Page title: {page.title()}")
            input("\nPress Enter to close the browser...")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def clean_profile(profile_dir: Optional[str] = None) -> int:
    """
    Remove cache and non-essential data from the profile to reduce export size.
    Keeps only what's needed for Google login (cookies, prefs, storage).

    Args:
        profile_dir: Profile directory to clean, or None for default

    Returns:
        Number of bytes freed
    """
    import shutil

    if profile_dir is None:
        profile_dir = get_default_profile_dir()
    else:
        profile_dir = os.path.expanduser(profile_dir)

    if not os.path.exists(profile_dir):
        return 0

    # Directories to delete entirely (pure cache/junk, not needed for login)
    junk_dirs = [
        'cache2',
        'thumbnails',
        'startupCache',
        'crashes',
        'minidumps',
        'datareporting',
        'saved-telemetry-pings',
        'healthreport',
        'security_state',
        'shader-cache',
        'gmp-clearkey',
        'gmp-widevinecdm',
    ]

    # Files to delete (large but not needed for session)
    junk_files = [
        'places.sqlite',       # browsing history
        'favicons.sqlite',     # favicons cache
        'webappsstore.sqlite', # web storage (non-login)
        'formhistory.sqlite',  # form history
    ]

    freed = 0

    for name in junk_dirs:
        path = os.path.join(profile_dir, name)
        if os.path.isdir(path):
            size = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, files in os.walk(path)
                for f in files
            )
            shutil.rmtree(path, ignore_errors=True)
            freed += size

    for name in junk_files:
        path = os.path.join(profile_dir, name)
        if os.path.isfile(path):
            freed += os.path.getsize(path)
            os.remove(path)

    return freed


def export_profile(source_dir: Optional[str] = None, dest_path: str = "./camoufox-profile.tar.gz", clean: bool = True) -> bool:
    """
    Export profile to a tar.gz file for portability (Docker, other machines, etc.)
    
    Args:
        source_dir: Source profile directory, or None for default
        dest_path: Destination file path for the exported profile
        clean: Remove cache/history before exporting to reduce file size (default: True)
        
    Returns:
        True if export successful
    """
    import tarfile
    
    if source_dir is None:
        source_dir = get_default_profile_dir()
    else:
        source_dir = os.path.expanduser(source_dir)
    
    if not is_profile_configured(source_dir):
        print(f"❌ Profile not configured at: {source_dir}")
        return False
    
    try:
        print(f"📦 Exporting profile from: {source_dir}")
        print(f"📁 To: {dest_path}")

        if clean:
            print("🧹 Cleaning cache and non-essential data...")
            freed = clean_profile(source_dir)
            print(f"   Freed: {freed / 1024 / 1024:.2f} MB")
        
        with tarfile.open(dest_path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        
        print(f"✅ Profile exported successfully!")
        print(f"📊 File size: {os.path.getsize(dest_path) / 1024 / 1024:.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def import_profile(source_path: str, dest_dir: Optional[str] = None) -> bool:
    """
    Import profile from a tar.gz file (for Docker, other machines, etc.)
    
    Args:
        source_path: Source tar.gz file path
        dest_dir: Destination profile directory, or None for default
        
    Returns:
        True if import successful
    """
    import tarfile
    
    if dest_dir is None:
        dest_dir = get_default_profile_dir()
    else:
        dest_dir = os.path.expanduser(dest_dir)
    
    if not os.path.exists(source_path):
        print(f"❌ Source file not found: {source_path}")
        return False
    
    try:
        print(f"📦 Importing profile from: {source_path}")
        print(f"📁 To: {dest_dir}")
        
        # Create parent directory if needed
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        
        with tarfile.open(source_path, "r:gz") as tar:
            tar.extractall(path=os.path.dirname(dest_dir))
        
        if is_profile_configured(dest_dir):
            print(f"✅ Profile imported successfully!")
            return True
        else:
            print(f"⚠️  Profile imported but may not be fully configured")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def print_profile_status(profile_dir: Optional[str] = None):
    """Print current profile configuration status"""
    if profile_dir is None:
        profile_dir = get_default_profile_dir()
    else:
        profile_dir = os.path.expanduser(profile_dir)
    
    print("=" * 70)
    print("🔍 Camoufox Profile Status")
    print("=" * 70)
    print(f"\n📁 Profile directory: {profile_dir}")
    
    if is_profile_configured(profile_dir):
        print("✅ Status: Configured")
        print("\n💡 Profile is ready to use with browser mode")
        print("\n📦 To use in Docker/other machines:")
        print("   1. Export: from pytrends_modern.camoufox_setup import export_profile")
        print("              export_profile(dest_path='profile.tar.gz')")
        print("   2. Copy profile.tar.gz to target machine/container")
        print("   3. Import: from pytrends_modern.camoufox_setup import import_profile")
        print("              import_profile('profile.tar.gz')")
    else:
        print("❌ Status: Not configured")
        print("\n⚠️  You need to run setup before using browser mode:")
        print("   from pytrends_modern.camoufox_setup import setup_profile")
        print("   setup_profile()")
        print("\n   Or use the CLI:")
        print("   python -m pytrends_modern.camoufox_setup")
    
    print("=" * 70)


if __name__ == "__main__":
    """Run setup when called as a module"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            print_profile_status()
        elif command == "test":
            success = test_profile()
            sys.exit(0 if success else 1)
        elif command == "clean":
            freed = clean_profile()
            print(f"🧹 Cleaned profile. Freed: {freed / 1024 / 1024:.2f} MB")
            sys.exit(0)
        elif command == "export":
            dest = sys.argv[2] if len(sys.argv) > 2 else "./camoufox-profile.tar.gz"
            success = export_profile(dest_path=dest)
            sys.exit(0 if success else 1)
        elif command == "import":
            if len(sys.argv) < 3:
                print("❌ Usage: python -m pytrends_modern.camoufox_setup import <source.tar.gz>")
                sys.exit(1)
            source = sys.argv[2]
            success = import_profile(source)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown command: {command}")
            print("\nUsage:")
            print("  python -m pytrends_modern.camoufox_setup          # Run setup")
            print("  python -m pytrends_modern.camoufox_setup status   # Check status")
            print("  python -m pytrends_modern.camoufox_setup test     # Open browser to test profile")
            print("  python -m pytrends_modern.camoufox_setup clean    # Remove cache/junk to free space")
            print("  python -m pytrends_modern.camoufox_setup export [path]  # Export profile")
            print("  python -m pytrends_modern.camoufox_setup import <path>  # Import profile")
            sys.exit(1)
    else:
        success = setup_profile()
        sys.exit(0 if success else 1)
