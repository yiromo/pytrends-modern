"""Browser configuration for Camoufox automation"""

from typing import Optional, Union, Dict, Any
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
                 - False: Show browser window (for local development)
                 - True: Standard headless mode (for servers with display)
                 - 'virtual': Use Xvfb virtual display (for Docker containers)
        proxy_server: Proxy server URL (e.g., 'http://proxy.com:8080')
        proxy_username: Proxy username (for authenticated proxies)
        proxy_password: Proxy password (for authenticated proxies)
        user_data_dir: Browser profile directory to persist login session.
                      Default: ~/.config/camoufox-pytrends
        humanize: Enable human-like cursor movement (default: True)
        os: Operating system for fingerprint ('windows', 'macos', 'linux')
        geoip: Auto-detect geolocation from proxy IP (default: True if proxy)
        rotate_fingerprint: Generate random fingerprint for each session (default: True)
                          Set to False to use persistent fingerprint
        min_delay: Minimum delay between requests in seconds (default: 2)
        max_delay: Maximum delay between requests in seconds (default: 5)
        persistent_context: Keep browser profile between sessions (default: True)
                          Set to False to use fresh profile each time (helps avoid 429)
    
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
        headless: Union[bool, str] = False,
        proxy_server: Optional[str] = None,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        humanize: bool = True,
        os: str = 'linux',
        geoip: bool = True,
        rotate_fingerprint: bool = True,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        persistent_context: bool = True,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        self.headless = headless
        self.proxy_server = proxy_server
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.user_data_dir = user_data_dir or os_module.path.expanduser('~/.config/camoufox-pytrends-profile')
        self.humanize = humanize
        self.os = os
        self.geoip = geoip if proxy_server else False
        self.rotate_fingerprint = rotate_fingerprint
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.persistent_context = persistent_context
        self.custom_config = custom_config or {}

