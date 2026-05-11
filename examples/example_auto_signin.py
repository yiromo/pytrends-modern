#!/usr/bin/env python3
"""
Example: Auto Google Sign-In with pytrends-modern

Use this when you don't have a saved profile yet (first run on a new machine,
Docker container, CI/CD) and want the browser to sign in automatically using
your Google account credentials.

Credentials are read from:
  1. google_password parameter in BrowserConfig
  2. GOOGLE_ACC_PASSWORD environment variable (recommended for CI/CD)

⚠️  SECURITY NOTES:
  - Never hard-code your password in source files.
  - Use environment variables or a secrets manager.
  - Don't commit files with credentials to git.

Usage:
  GOOGLE_ACC_PASSWORD="your_password" python examples/example_auto_signin.py
"""

import os

# ---------------------------------------------------------------------------
# Option A: Auto sign-in via environment variable (recommended)
# ---------------------------------------------------------------------------
# print("=" * 70)
# print("Option A: Auto sign-in via GOOGLE_ACC_PASSWORD environment variable")
# print("=" * 70)

# password = os.environ.get("GOOGLE_ACC_PASSWORD")
# if not password:
#     print("\n⚠️  GOOGLE_ACC_PASSWORD not set. Skipping Option A.")
#     print("   Set it with: export GOOGLE_ACC_PASSWORD='your_password'")
# else:
#     from pytrends_modern import TrendReq, BrowserConfig

#     config = BrowserConfig(
#         headless=False,          # Set True on servers, "virtual" for Docker
#         google_sign_in=True,     # Enable auto sign-in
#         # google_password not needed — read from GOOGLE_ACC_PASSWORD env var
#     )

#     try:
#         pytrends = TrendReq(browser_config=config)
#         pytrends.kw_list = ['Python']
#         df = pytrends.interest_over_time()
#         print("\n✅ Success!")
#         print(df.head())
#     except Exception as e:
#         print(f"\n❌ Error: {e}")

# ---------------------------------------------------------------------------
# Option B: Auto sign-in with password in BrowserConfig
#           (only for local scripts — never commit this to git)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("Option B: Auto sign-in with google_password in BrowserConfig")
print("=" * 70)
print("⚠️  Shown for completeness. Use env var in production.\n")

from pytrends_modern import TrendReq, BrowserConfig

config = BrowserConfig(
    headless=False,
    google_sign_in=True,
    google_password="qwe123qwe123",   # ← never commit this!
)

pytrends = TrendReq(browser_config=config)
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
print(df.head())

# ---------------------------------------------------------------------------
# Option C: Auto sign-in during profile setup (one-time, then reuse profile)
# ---------------------------------------------------------------------------
print("=" * 70)
print("Option C: Auto sign-in during setup_profile() — saves session for reuse")
print("=" * 70)
print("""
# Run once to sign in and save the profile:
from pytrends_modern.camoufox_setup import setup_profile
import os

setup_profile(
    google_sign_in=True,
    google_password=os.environ.get("GOOGLE_ACC_PASSWORD"),
)

# After setup, use normally (no credentials needed):
from pytrends_modern import TrendReq, BrowserConfig
config = BrowserConfig()   # google_sign_in not needed — session is saved
pytrends = TrendReq(browser_config=config)
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
print(df.head())
""")

# ---------------------------------------------------------------------------
# Option D: Docker / CI — headless with virtual display
# ---------------------------------------------------------------------------
print("=" * 70)
print("Option D: Docker / headless server usage")
print("=" * 70)
print("""
# In Docker or CI, use headless='virtual' (requires Xvfb):
from pytrends_modern import TrendReq, BrowserConfig
import os

config = BrowserConfig(
    headless="virtual",      # Xvfb virtual display for Docker
    google_sign_in=True,
    # password from GOOGLE_ACC_PASSWORD env var
)

pytrends = TrendReq(browser_config=config)
pytrends.kw_list = ['Python']
df = pytrends.interest_over_time()
print(df.head())
""")
