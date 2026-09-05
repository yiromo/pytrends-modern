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


def _resolve_google_password(config_password: Optional[str] = None) -> Optional[str]:
    """Resolve Google password from config param or environment variable."""
    return config_password or os.environ.get("GOOGLE_ACC_PASSWORD")


def _resolve_google_email(config_email: Optional[str] = None) -> Optional[str]:
    """Resolve Google account email from config param or environment variable."""
    return config_email or os.environ.get("GOOGLE_ACC_EMAIL")


IDENTIFIER_INPUT_SELECTOR = '#identifierId, input[type="email"], input[name="identifier"]'


def _find_sign_in_button(page) -> bool:
    """
    Check if a 'Sign in' link is present on the page.

    Checks for aria-label in multiple languages:
    - "Sign in" (English)
    - "Anmelden" (German)
    - "Войти" (Russian)

    Uses CSS selectors first, falls back to XPath.

    Returns:
        True if sign-in button found and visible, False otherwise.
    """
    sign_in_labels = ["Sign in", "Anmelden", "Войти"]
    for label in sign_in_labels:
        try:
            locator = page.locator(f'a[aria-label="{label}"]')
            if locator.count() > 0 and locator.first.is_visible():
                return True
        except Exception:
            pass

    try:
        xpath = '/html/body/div[3]/header/div[2]/div[3]/div[1]/a'
        locator = page.locator(f'xpath={xpath}')
        if locator.count() > 0:
            text_content = locator.first.text_content()
            if text_content and any(
                label.lower() in text_content.lower() for label in sign_in_labels
            ):
                return True
    except Exception:
        pass

    return False


def _click_sign_in_button(page) -> bool:
    """Click the 'Sign in' button on Google Trends page."""
    sign_in_labels = ["Sign in", "Anmelden", "Войти"]
    for label in sign_in_labels:
        try:
            locator = page.locator(f'a[aria-label="{label}"]')
            if locator.count() > 0 and locator.first.is_visible():
                locator.first.click()
                return True
        except Exception:
            pass

    try:
        xpath = '/html/body/div[3]/header/div[2]/div[3]/div[1]/a'
        locator = page.locator(f'xpath={xpath}')
        if locator.count() > 0:
            locator.first.click()
            return True
    except Exception:
        pass

    return False


def _click_first_account(page, timeout: float = 5.0) -> bool:
    """Click the first account in the Google account chooser."""
    try:
        account_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[2]/div/div/div/span/section/div/div/div/div/ul/li[1]'
        )
        first_account = page.locator(f'xpath={account_xpath}')
        first_account.wait_for(state="visible", timeout=timeout * 1000)
        first_account.click()
        return True
    except Exception:
        pass

    try:
        if page.locator(IDENTIFIER_INPUT_SELECTOR).count() > 0:
            return False
        list_items = page.locator('ul li')
        if list_items.count() > 0:
            list_items.first.click()
            return True
    except Exception:
        pass

    return False


def _fill_password(page, password: str, timeout: float = 5.0) -> bool:
    """Fill the password input field."""
    try:
        pw_input = page.locator('input[type="password"]')
        pw_input.wait_for(state="visible", timeout=timeout * 1000)
        pw_input.fill(password)
        return True
    except Exception:
        pass

    try:
        pw_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[2]/div/div/div/span/section[2]/div/div/div[1]'
            '/div[1]/div/div/div/div/div[1]/div/div[1]/input'
        )
        pw_input = page.locator(f'xpath={pw_xpath}')
        pw_input.wait_for(state="visible", timeout=timeout * 1000)
        pw_input.fill(password)
        return True
    except Exception:
        pass

    return False


def _fill_email(page, email: str, timeout: float = 5.0) -> bool:
    """Fill the email input on the sign-in 'identifier' page.

    Google shows this page instead of the account chooser when the profile has
    no remembered account (e.g. the session was revoked server-side).
    """
    for selector in ('#identifierId', 'input[type="email"]', 'input[name="identifier"]'):
        try:
            email_input = page.locator(selector)
            email_input.wait_for(state="visible", timeout=timeout * 1000)
            email_input.fill(email)
            return True
        except Exception:
            pass

    return False


def _click_next_button(page, timeout: float = 5.0) -> bool:
    """Click the 'Next' / 'Weiter' button after entering password."""
    next_labels = ["Next", "Weiter", "Далее"]
    for label in next_labels:
        try:
            btn = page.locator(f'button:has-text("{label}")')
            if btn.count() > 0:
                btn.first.click()
                return True
        except Exception:
            pass

    try:
        next_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[3]/div/div[1]/div/div/button/span'
        )
        btn = page.locator(f'xpath={next_xpath}')
        btn.wait_for(state="visible", timeout=timeout * 1000)
        parent_btn = btn.locator('xpath=..')
        parent_btn.click()
        return True
    except Exception:
        pass

    try:
        btn = page.locator('button div[role="button"]')
        if btn.count() > 0:
            btn.first.click()
            return True
    except Exception:
        pass

    return False


def auto_google_sign_in(
    page, password: str, step_timeout: float = 5.0, email: Optional[str] = None
) -> bool:
    """
    Automatically sign in to Google if a 'Sign in' button is detected.

    This function checks if the user is logged in by looking for the sign-in
    link on Google Trends. If found, it performs the full login flow:
    1. Click "Sign in" button
    2. Select the account — from the chooser, or by entering `email` when
       Google shows the identifier page instead (profile lost its remembered
       account, e.g. after a server-side session revocation)
    3. Enter password
    4. Click "Next"

    If no sign-in button is found, the user is already logged in and
    the function returns True immediately.

    Args:
        page: Playwright Page object (from Camoufox context).
        password: Google account password.
        step_timeout: Timeout in seconds for each step (default: 5.0).
        email: Account email for the identifier page fallback (optional but
               strongly recommended — without it a signed-out profile cannot
               recover).

    Returns:
        True if sign-in completed successfully or user was already signed in.

    Raises:
        Exception: If a required step fails (with descriptive message).
    """
    if not _find_sign_in_button(page):
        return True

    if not _click_sign_in_button(page):
        raise Exception("Auto sign-in failed: Could not click 'Sign in' button")
    page.wait_for_timeout(1500)

    if not _click_first_account(page, timeout=step_timeout):
        if not email or not _fill_email(page, email, timeout=step_timeout):
            raise Exception(
                "Auto sign-in failed: Could not select account from the list"
                + ("" if email else " (no account email configured for the identifier page)")
            )
        page.wait_for_timeout(500)
        if not _click_next_button(page, timeout=step_timeout):
            raise Exception("Auto sign-in failed: Could not click 'Next' after email")
    page.wait_for_timeout(1500)

    if not _fill_password(page, password, timeout=step_timeout):
        raise Exception("Auto sign-in failed: Could not find or fill password input")
    page.wait_for_timeout(500)

    if not _click_next_button(page, timeout=step_timeout):
        raise Exception("Auto sign-in failed: Could not click 'Next' button after password")
    page.wait_for_timeout(1500)

    if _find_sign_in_button(page):
        raise Exception(
            "Auto sign-in failed: 'Sign in' button still present after login. "
            "The password may be incorrect or additional verification is required."
        )

    return True


async def _afind_sign_in_button(page) -> bool:
    """Async version of _find_sign_in_button."""
    sign_in_labels = ["Sign in", "Anmelden", "Войти"]
    for label in sign_in_labels:
        try:
            locator = page.locator(f'a[aria-label="{label}"]')
            if await locator.count() > 0 and await locator.first.is_visible():
                return True
        except Exception:
            pass

    try:
        xpath = '/html/body/div[3]/header/div[2]/div[3]/div[1]/a'
        locator = page.locator(f'xpath={xpath}')
        if await locator.count() > 0:
            text_content = await locator.first.text_content()
            if text_content and any(
                label.lower() in text_content.lower() for label in sign_in_labels
            ):
                return True
    except Exception:
        pass

    return False


async def _aclick_sign_in_button(page) -> bool:
    """Async version of _click_sign_in_button."""
    sign_in_labels = ["Sign in", "Anmelden", "Войти"]
    for label in sign_in_labels:
        try:
            locator = page.locator(f'a[aria-label="{label}"]')
            if await locator.count() > 0 and await locator.first.is_visible():
                await locator.first.click()
                return True
        except Exception:
            pass

    try:
        xpath = '/html/body/div[3]/header/div[2]/div[3]/div[1]/a'
        locator = page.locator(f'xpath={xpath}')
        if await locator.count() > 0:
            await locator.first.click()
            return True
    except Exception:
        pass

    return False


async def _aclick_first_account(page, timeout: float = 5.0) -> bool:
    """Async version of _click_first_account."""
    try:
        account_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[2]/div/div/div/span/section/div/div/div/div/ul/li[1]'
        )
        first_account = page.locator(f'xpath={account_xpath}')
        await first_account.wait_for(state="visible", timeout=timeout * 1000)
        await first_account.click()
        return True
    except Exception:
        pass

    try:
        if await page.locator(IDENTIFIER_INPUT_SELECTOR).count() > 0:
            return False
        list_items = page.locator('ul li')
        if await list_items.count() > 0:
            await list_items.first.click()
            return True
    except Exception:
        pass

    return False


async def _afill_password(page, password: str, timeout: float = 5.0) -> bool:
    """Async version of _fill_password."""
    try:
        pw_input = page.locator('input[type="password"]')
        await pw_input.wait_for(state="visible", timeout=timeout * 1000)
        await pw_input.fill(password)
        return True
    except Exception:
        pass

    try:
        pw_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[2]/div/div/div/span/section[2]/div/div/div[1]'
            '/div[1]/div/div/div/div/div[1]/div/div[1]/input'
        )
        pw_input = page.locator(f'xpath={pw_xpath}')
        await pw_input.wait_for(state="visible", timeout=timeout * 1000)
        await pw_input.fill(password)
        return True
    except Exception:
        pass

    return False


async def _afill_email(page, email: str, timeout: float = 5.0) -> bool:
    """Async version of _fill_email."""
    for selector in ('#identifierId', 'input[type="email"]', 'input[name="identifier"]'):
        try:
            email_input = page.locator(selector)
            await email_input.wait_for(state="visible", timeout=timeout * 1000)
            await email_input.fill(email)
            return True
        except Exception:
            pass

    return False


async def _aclick_next_button(page, timeout: float = 5.0) -> bool:
    """Async version of _click_next_button."""
    next_labels = ["Next", "Weiter", "Далее"]
    for label in next_labels:
        try:
            btn = page.locator(f'button:has-text("{label}")')
            if await btn.count() > 0:
                await btn.first.click()
                return True
        except Exception:
            pass

    try:
        next_xpath = (
            '/html/body/div[2]/div[1]/div[1]/div[2]/c-wiz/main'
            '/div[3]/div/div[1]/div/div/button/span'
        )
        btn = page.locator(f'xpath={next_xpath}')
        await btn.wait_for(state="visible", timeout=timeout * 1000)
        parent_btn = btn.locator('xpath=..')
        await parent_btn.click()
        return True
    except Exception:
        pass

    try:
        btn = page.locator('button div[role="button"]')
        if await btn.count() > 0:
            await btn.first.click()
            return True
    except Exception:
        pass

    return False


async def auto_google_sign_in_async(
    page, password: str, step_timeout: float = 5.0, email: Optional[str] = None
) -> bool:
    """
    Async version of auto_google_sign_in.

    Same logic but awaits all Playwright calls. Use this with async
    Camoufox pages (AsyncTrendReq).
    """
    if not await _afind_sign_in_button(page):
        return True

    if not await _aclick_sign_in_button(page):
        raise Exception("Auto sign-in failed: Could not click 'Sign in' button")
    await page.wait_for_timeout(1500)

    if not await _aclick_first_account(page, timeout=step_timeout):
        if not email or not await _afill_email(page, email, timeout=step_timeout):
            raise Exception(
                "Auto sign-in failed: Could not select account from the list"
                + ("" if email else " (no account email configured for the identifier page)")
            )
        await page.wait_for_timeout(500)
        if not await _aclick_next_button(page, timeout=step_timeout):
            raise Exception("Auto sign-in failed: Could not click 'Next' after email")
    await page.wait_for_timeout(1500)

    if not await _afill_password(page, password, timeout=step_timeout):
        raise Exception("Auto sign-in failed: Could not find or fill password input")
    await page.wait_for_timeout(500)

    if not await _aclick_next_button(page, timeout=step_timeout):
        raise Exception("Auto sign-in failed: Could not click 'Next' button after password")
    await page.wait_for_timeout(1500)

    if await _afind_sign_in_button(page):
        raise Exception(
            "Auto sign-in failed: 'Sign in' button still present after login. "
            "The password may be incorrect or additional verification is required."
        )

    return True


def setup_profile(
    profile_dir: Optional[str] = None,
    headless: bool = False,
    google_sign_in: bool = False,
    google_password: Optional[str] = None,
    google_email: Optional[str] = None,
) -> bool:
    """
    Interactive setup: Open browser for user to log in to Google

    Args:
        profile_dir: Custom profile directory, or None for default
        headless: Run in headless mode (not recommended for first setup)
        google_sign_in: Automatically sign in using provided password
        google_password: Google account password (falls back to GOOGLE_ACC_PASSWORD env var)
        google_email: Account email for the identifier page (falls back to GOOGLE_ACC_EMAIL env var)

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

    resolved_password = _resolve_google_password(google_password) if google_sign_in else None
    if google_sign_in and not resolved_password:
        print("\n❌ Error: google_sign_in=True but no password provided.")
        print("   Set google_password parameter or GOOGLE_ACC_PASSWORD env var.")
        return False

    if is_profile_configured(profile_dir):
        print("✓ Profile already exists")
        if google_sign_in:
            print("   Checking if Google session is still valid...")
        else:
            response = input("\nReconfigure profile? This will open the browser again (y/N): ")
            if response.lower() != 'y':
                print("Setup cancelled.")
                return False

    if google_sign_in:
        print("\n🤖 Auto sign-in enabled")
        print("   Browser will sign in automatically using provided credentials.")
    else:
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
            geoip=False,
        ) as context:
            page = context.pages[0] if context.pages else context.new_page()
            
            print("\n🌐 Opening Google Trends...")
            
            # Navigate to Google Trends
            page.goto(
                "https://trends.google.com/trends/explore?q=Python&legacy&hl=en-GB",
                wait_until='networkidle',
                timeout=60000
            )
            
            title = page.title()
            if "429" in title or "error" in title.lower():
                print(f"\n⚠️  Page title: {title}")
                print("   You may need to log in or solve a CAPTCHA")
            else:
                print(f"✓ Page loaded: {title}")

            if google_sign_in and resolved_password:
                try:
                    auto_google_sign_in(
                        page, resolved_password, email=_resolve_google_email(google_email)
                    )
                    print("✅ Auto sign-in completed successfully")
                except Exception as e:
                    print(f"❌ Auto sign-in failed: {e}")
                    if headless:
                        print("   Manual login is not possible in headless mode.")
                        return False
                    print("   Falling back to manual login...")
                    google_sign_in = False

            if not google_sign_in:
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
    import tempfile
    import shutil

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

        parent = os.path.dirname(dest_dir)
        os.makedirs(parent, exist_ok=True)

        # Extract to a temp dir first: the tar's internal root directory no
        # longer has to match dest_dir's basename.
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            with tarfile.open(source_path, "r:gz") as tar:
                tar.extractall(path=tmp)

            entries = os.listdir(tmp)
            if len(entries) == 1 and os.path.isdir(os.path.join(tmp, entries[0])):
                src_root = os.path.join(tmp, entries[0])
            else:
                src_root = tmp

            if not is_profile_configured(src_root):
                print("❌ Archive does not contain a Camoufox profile; existing profile left untouched")
                return False

            # Replace, never merge: leftovers from a previous session (sqlite
            # -wal/-shm journals, locks) would survive a merge and clobber the
            # freshly imported databases on the next browser start.
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            if src_root == tmp:
                shutil.copytree(tmp, dest_dir)
            else:
                shutil.move(src_root, dest_dir)

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
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Camoufox profile setup for pytrends-modern")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Check profile status")

    subparsers.add_parser("test", help="Open browser to test profile")

    subparsers.add_parser("clean", help="Remove cache/junk to free space")

    export_parser = subparsers.add_parser("export", help="Export profile to tar.gz")
    export_parser.add_argument("path", nargs="?", default="./camoufox-profile.tar.gz", help="Destination path")

    import_parser = subparsers.add_parser("import_profile", help="Import profile from tar.gz")
    import_parser.add_argument("path", help="Source tar.gz file")

    auto_parser = subparsers.add_parser("auto-signin", help="Auto sign-in with Google password")
    auto_parser.add_argument("--password", "-p", default=None, help="Google password (or set GOOGLE_ACC_PASSWORD env var)")
    auto_parser.add_argument("--email", "-e", default=None, help="Google account email for the identifier page (or set GOOGLE_ACC_EMAIL env var)")
    auto_parser.add_argument("--headless", action="store_true", help="Run in headless mode")

    subparsers.add_parser("setup", help="Interactive manual setup")

    args = parser.parse_args()

    if args.command == "status":
        print_profile_status()
    elif args.command == "test":
        success = test_profile()
        sys.exit(0 if success else 1)
    elif args.command == "clean":
        freed = clean_profile()
        print(f"🧹 Cleaned profile. Freed: {freed / 1024 / 1024:.2f} MB")
        sys.exit(0)
    elif args.command == "export":
        success = export_profile(dest_path=args.path)
        sys.exit(0 if success else 1)
    elif args.command == "import_profile":
        success = import_profile(args.path)
        sys.exit(0 if success else 1)
    elif args.command == "auto-signin":
        password = args.password or os.environ.get("GOOGLE_ACC_PASSWORD")
        if not password:
            print("❌ No password provided. Use --password or set GOOGLE_ACC_PASSWORD env var.")
            sys.exit(1)
        success = setup_profile(
            google_sign_in=True,
            google_password=password,
            google_email=args.email,
            headless=args.headless,
        )
        sys.exit(0 if success else 1)
    elif args.command == "setup":
        success = setup_profile()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
