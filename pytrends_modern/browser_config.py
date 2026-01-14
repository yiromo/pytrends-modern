"""Browser configuration for DrissionPage automation."""

from typing import Optional


class BrowserConfig:
    """Configuration for DrissionPage browser automation.
    
    When enabled, TrendReq will use DrissionPage to capture network traffic
    from trends.google.com instead of making direct API calls.
    
    ⚠️ LIMITATIONS when using BrowserConfig:
    - Only 1 keyword supported (no comparison)
    - Only 'today 1-m' timeframe supported
    - Only WORLDWIDE geo supported (no geo filtering)
    - Requires Chrome/Chromium browser installed
    
    Args:
        browser_path: Path to Chrome/Chromium executable.
                     Defaults: '/usr/bin/chromium' or '/usr/bin/chrome'
        port: Browser remote debugging port (default: 9222)
        headless: Run browser in headless mode (default: True)
        proxy: Proxy server URL (e.g., 'http://proxy.com:8080')
        proxy_username: Proxy username (for authenticated proxies)
        proxy_password: Proxy password (for authenticated proxies)
        user_data_dir: Browser profile directory to persist login session.
                      If not provided, creates temp directory (won't persist)
    
    Example:
        >>> from pytrends_modern import TrendReq, BrowserConfig
        >>> # Without auth - manual login required once
        >>> config = BrowserConfig(
        ...     browser_path='/usr/bin/chromium',
        ...     user_data_dir='~/.config/chromium-pytrends'
        ... )
        >>> # With proxy auth
        >>> config = BrowserConfig(
        ...     browser_path='/usr/bin/chromium',
        ...     proxy='153.80.44.3:64804',
        ...     proxy_username='user',
        ...     proxy_password='pass',
        ...     user_data_dir='~/.config/chromium-pytrends'
        ... )
        >>> pytrends = TrendReq(browser_config=config)
        >>> pytrends.build_payload(['Python'])  # Only 1 keyword!
        >>> df = pytrends.interest_over_time()
    """
    
    def __init__(
        self,
        browser_path: Optional[str] = None,
        port: int = 9222,
        headless: bool = True,
        proxy: Optional[str] = None,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
        user_data_dir: Optional[str] = None
    ):
        self.browser_path = browser_path or self._get_default_browser_path()
        self.port = port
        self.headless = headless
        self.proxy = proxy
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.user_data_dir = user_data_dir
    
    @staticmethod
    def _get_default_browser_path() -> str:
        """Get default browser path based on common locations."""
        import os
        
        # Common Chrome/Chromium paths
        paths = [
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/chrome',
            '/usr/bin/google-chrome',
            '/snap/bin/chromium',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Default fallback
        return '/usr/bin/chromium'
    
    def __repr__(self) -> str:
        return (
            f"BrowserConfig(browser_path='{self.browser_path}', "
            f"port={self.port}, headless={self.headless}, proxy={self.proxy})"
        )
