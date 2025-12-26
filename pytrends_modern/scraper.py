"""
Selenium-based scraper for Google Trends trending searches
Uses browser automation to download CSV data when API endpoints are unavailable
"""

import os
import time
from typing import Optional, Union, List, Dict
from pathlib import Path
import warnings

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
)

from . import exceptions


class TrendsScraper:
    """
    Selenium-based scraper for Google Trends when API endpoints are unavailable

    This provides an alternative to deprecated API methods like trending_searches()
    by using browser automation to download actual trending data.
    """

    def __init__(self, headless: bool = True, download_dir: Optional[str] = None):
        """
        Initialize the scraper

        Args:
            headless: Run browser in headless mode
            download_dir: Directory for downloads (default: temp directory)
        """
        self.headless = headless

        if download_dir is None:
            import tempfile

            self.download_dir = tempfile.mkdtemp(prefix="pytrends_")
        else:
            self.download_dir = os.path.abspath(download_dir)
            os.makedirs(self.download_dir, exist_ok=True)

        self.driver = None

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if self.driver is not None:
            return

        chrome_options = Options()
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except WebDriverException as e:
            raise exceptions.BrowserError(
                f"Failed to start Chrome browser: {e}\n\n"
                "Please ensure:\n"
                "1. Chrome/Chromium browser is installed\n"
                "2. ChromeDriver is compatible with your Chrome version\n"
                "3. You have proper permissions\n"
            )

    def trending_searches(
        self,
        geo: str = "US",
        hours: int = 24,
        category: str = "all",
        active_only: bool = False,
        sort_by: str = "relevance",
        return_df: bool = True,
    ) -> Union[pd.DataFrame, str]:
        """
        Get trending searches by scraping Google Trends

        Args:
            geo: Country code (US, GB, IN, etc.)
            hours: Time period in hours (4, 24, 48, 168)
            category: Category filter (all, sports, entertainment, etc.)
            active_only: Show only active trends
            sort_by: Sort criteria (relevance, title, volume, recency)
            return_df: Return DataFrame (True) or CSV path (False)

        Returns:
            DataFrame of trending searches or path to CSV file

        Raises:
            BrowserError: If browser automation fails
            DownloadError: If download fails

        Example:
            >>> scraper = TrendsScraper()
            >>> df = scraper.trending_searches(geo='US', hours=24)
            >>> print(df.head())
        """
        self._init_driver()

        # Get existing files before download
        existing_files = set(f for f in os.listdir(self.download_dir) if f.endswith(".csv"))

        try:
            # Build URL with parameters
            url = f"https://trends.google.com/trending?geo={geo}"

            if hours != 24:
                url += f"&hours={hours}"

            # Add category if not 'all'
            categories = {
                "all": "",
                "business": "b",
                "entertainment": "e",
                "health": "m",
                "science": "t",
                "sports": "s",
                "top": "h",
            }
            cat_code = categories.get(category.lower(), "")
            if cat_code:
                url += f"&cat={cat_code}"

            # Navigate to page
            self.driver.get(url)

            # Wait for page to load by checking for Export button
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Export')]"))
            )

            # Click Export button
            try:
                export_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export')]"))
                )
                export_button.click()
                time.sleep(1)

                # Click Download CSV from the menu
                download_csv = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-action="csv"]'))
                )
                self.driver.execute_script("arguments[0].click();", download_csv)
                time.sleep(1)

            except Exception as e:
                raise exceptions.DownloadError(f"Could not find or click Export/CSV button: {e}")

            # Wait for file download
            max_wait = 30
            waited = 0
            downloaded_file = None

            while waited < max_wait:
                current_files = set(f for f in os.listdir(self.download_dir) if f.endswith(".csv"))
                new_files = current_files - existing_files

                if new_files:
                    # Get the most recently created file
                    newest = max(
                        new_files,
                        key=lambda f: os.path.getctime(os.path.join(self.download_dir, f)),
                    )
                    downloaded_file = os.path.join(self.download_dir, newest)

                    # Verify file is complete (size > 0 and not growing)
                    size1 = os.path.getsize(downloaded_file)
                    time.sleep(0.5)
                    size2 = os.path.getsize(downloaded_file)

                    if size1 > 0 and size1 == size2:
                        break

                time.sleep(0.5)
                waited += 0.5

            if not downloaded_file:
                raise exceptions.DownloadError(
                    f"Download timeout after {max_wait}s. No CSV file appeared in {self.download_dir}"
                )

            # Return DataFrame or path
            if return_df:
                df = pd.read_csv(downloaded_file)
                # Clean up file
                try:
                    os.remove(downloaded_file)
                except:
                    pass
                return df
            else:
                return downloaded_file

        except Exception as e:
            if isinstance(e, (exceptions.BrowserError, exceptions.DownloadError)):
                raise
            raise exceptions.DownloadError(f"Scraping failed: {e}")

    def today_searches(self, geo: str = "US", return_df: bool = True) -> Union[pd.DataFrame, str]:
        """
        Get today's trending searches (shortcut for 24 hour trends)

        Args:
            geo: Country code (US, GB, IN, etc.)
            return_df: Return DataFrame (True) or CSV path (False)

        Returns:
            DataFrame of today's trending searches

        Example:
            >>> scraper = TrendsScraper()
            >>> df = scraper.today_searches(geo='US')
        """
        return self.trending_searches(geo=geo, hours=24, return_df=return_df)

    def realtime_trending_searches(
        self, geo: str = "US", hours: int = 4, return_df: bool = True
    ) -> Union[pd.DataFrame, str]:
        """
        Get real-time trending searches (4 hour window)

        Args:
            geo: Country code (US, GB, IN, etc.)
            hours: Time period (default 4 for real-time)
            return_df: Return DataFrame (True) or CSV path (False)

        Returns:
            DataFrame of real-time trending searches

        Example:
            >>> scraper = TrendsScraper()
            >>> df = scraper.realtime_trending_searches(geo='US')
        """
        return self.trending_searches(geo=geo, hours=hours, return_df=return_df)

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()

    def close(self):
        # Ignore errors during shutdown
        """Close browser and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

        # Cleanup temp directory if we created it
        if self.download_dir and "/tmp/" in self.download_dir:
            import shutil

            try:
                shutil.rmtree(self.download_dir)
            except:
                pass

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.close()
        except:
            pass
