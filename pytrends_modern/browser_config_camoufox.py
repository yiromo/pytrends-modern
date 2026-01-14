"""Browser configuration for Camoufox automation"""

from typing import Optional
import os as os_module


class BrowserConfig:
    """Configuration for Camoufox browser automation.
    
    Uses Camoufox (Playwright Firefox) with advanced fingerprinting and
    anti-detection to bypass Google's bot detection.
    
    ⚠️ LIMITATIONS:
    - Only 1 keyword supported (no comparison)
    - Only 'today 1-m' timeframe supported
    - Only WORLDWIDE geo supported (no geo filtering)
    - Requires Google account login (first run)
    
    Args:
        headless: Run browser in headless mode (default: False)
                 Set to 'virtual' on Linux to use Xvfb
        proxy_server: Proxy server URL (e.g., 'http://proxy.com:8080')
        proxy_username: Proxy username (for authenticated proxies)
        proxy_password: Proxy password (for authenticated proxies)
        user_data_dir: Browser profile directory to persist login session.
                      Default: ~/.config/camoufox-pytrends
        humanize: Enable human-like cursor movement (default: True)
        os: Operating system for fingerprint ('windows', 'macos', 'linux')
        geoip: Auto-detect geolocation from proxy IP (default: True if proxy)
    
    Example:
        >>> from pytrends_modern import TrendReq, BrowserConfig
        >>> # Simple usage (logs in once, saves session)
        >>> config = BrowserConfig()
        >>> pytrends = TrendReq(browser_config=config)
        >>> pytrends.build_payload(['Python'])
        >>> df = pytrends.interest_over_time()
        >>>
        >>> # With proxy
        >>> config = BrowserConfig(
        ...     proxy_server='http://proxy.com:8080',
        ...     proxy_username='user',
        ...     proxy_password='pass',
        ...     geoip=True
        ... )
    """
    
    def __init__(
        self,
        headless: bool = False,
        proxy_server: Optional[str] = None,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        humanize: bool = True,
        os: str = 'linux',
        geoip: bool = True,
    ):
        self.headless = headless
        self.proxy_server = proxy_server
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.user_data_dir = user_data_dir or os_module.path.expanduser('~/.config/camoufox-pytrends-profile')
        self.humanize = humanize
        self.os = os
        self.geoip = geoip if proxy_server else False

