"""
Configuration and constants for pytrends-modern
"""

from typing import Dict

# Base URL for Google Trends
BASE_TRENDS_URL = "https://trends.google.com/trends"

# API Endpoints
GENERAL_URL = f"{BASE_TRENDS_URL}/api/explore"
INTEREST_OVER_TIME_URL = f"{BASE_TRENDS_URL}/api/widgetdata/multiline"
MULTIRANGE_INTEREST_OVER_TIME_URL = f"{BASE_TRENDS_URL}/api/widgetdata/multirange"
INTEREST_BY_REGION_URL = f"{BASE_TRENDS_URL}/api/widgetdata/comparedgeo"
RELATED_QUERIES_URL = f"{BASE_TRENDS_URL}/api/widgetdata/relatedsearches"
TRENDING_SEARCHES_URL = f"{BASE_TRENDS_URL}/hottrends/visualize/internal/data"
TOP_CHARTS_URL = f"{BASE_TRENDS_URL}/api/topcharts"
SUGGESTIONS_URL = f"{BASE_TRENDS_URL}/api/autocomplete/"
CATEGORIES_URL = f"{BASE_TRENDS_URL}/api/explore/pickers/category"
TODAY_SEARCHES_URL = f"{BASE_TRENDS_URL}/api/dailytrends"
REALTIME_TRENDING_SEARCHES_URL = f"{BASE_TRENDS_URL}/api/realtimetrends"

# HTTP Error codes to retry
ERROR_CODES = (500, 502, 504, 429)

# Default values
DEFAULT_TIMEOUT = (10, 25)  # (connect, read) in seconds
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.3
DEFAULT_HL = "en-US"
DEFAULT_TZ = 360
DEFAULT_GEO = ""

# Valid gprop values
VALID_GPROP = ["", "images", "news", "youtube", "froogle"]

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Countries for RSS and geo filtering
COUNTRIES: Dict[str, str] = {
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "IN": "India",
    "DE": "Germany",
    "FR": "France",
    "ES": "Spain",
    "IT": "Italy",
    "BR": "Brazil",
    "MX": "Mexico",
    "AR": "Argentina",
    "JP": "Japan",
    "KR": "South Korea",
    "CN": "China",
    "RU": "Russia",
    "ZA": "South Africa",
    "NL": "Netherlands",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "PL": "Poland",
    "TR": "Turkey",
    "SA": "Saudi Arabia",
    "AE": "United Arab Emirates",
    "SG": "Singapore",
    "MY": "Malaysia",
    "TH": "Thailand",
    "ID": "Indonesia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "NZ": "New Zealand",
    "IE": "Ireland",
    "BE": "Belgium",
    "CH": "Switzerland",
    "AT": "Austria",
    "PT": "Portugal",
    "GR": "Greece",
    "CZ": "Czech Republic",
    "RO": "Romania",
    "HU": "Hungary",
    "IL": "Israel",
    "EG": "Egypt",
    "NG": "Nigeria",
    "KE": "Kenya",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "VE": "Venezuela",
}

# US States
US_STATES: Dict[str, str] = {
    "US-AL": "Alabama",
    "US-AK": "Alaska",
    "US-AZ": "Arizona",
    "US-AR": "Arkansas",
    "US-CA": "California",
    "US-CO": "Colorado",
    "US-CT": "Connecticut",
    "US-DE": "Delaware",
    "US-FL": "Florida",
    "US-GA": "Georgia",
    "US-HI": "Hawaii",
    "US-ID": "Idaho",
    "US-IL": "Illinois",
    "US-IN": "Indiana",
    "US-IA": "Iowa",
    "US-KS": "Kansas",
    "US-KY": "Kentucky",
    "US-LA": "Louisiana",
    "US-ME": "Maine",
    "US-MD": "Maryland",
    "US-MA": "Massachusetts",
    "US-MI": "Michigan",
    "US-MN": "Minnesota",
    "US-MS": "Mississippi",
    "US-MO": "Missouri",
    "US-MT": "Montana",
    "US-NE": "Nebraska",
    "US-NV": "Nevada",
    "US-NH": "New Hampshire",
    "US-NJ": "New Jersey",
    "US-NM": "New Mexico",
    "US-NY": "New York",
    "US-NC": "North Carolina",
    "US-ND": "North Dakota",
    "US-OH": "Ohio",
    "US-OK": "Oklahoma",
    "US-OR": "Oregon",
    "US-PA": "Pennsylvania",
    "US-RI": "Rhode Island",
    "US-SC": "South Carolina",
    "US-SD": "South Dakota",
    "US-TN": "Tennessee",
    "US-TX": "Texas",
    "US-UT": "Utah",
    "US-VT": "Vermont",
    "US-VA": "Virginia",
    "US-WA": "Washington",
    "US-WV": "West Virginia",
    "US-WI": "Wisconsin",
    "US-WY": "Wyoming",
    "US-DC": "District of Columbia",
}

# Categories mapping
CATEGORIES: Dict[str, int] = {
    "all": 0,
    "arts_entertainment": 3,
    "autos_vehicles": 47,
    "beauty_fitness": 44,
    "books_literature": 22,
    "business_industrial": 7,
    "computers_electronics": 5,
    "finance": 7,
    "food_drink": 71,
    "games": 8,
    "health": 45,
    "hobbies_leisure": 65,
    "home_garden": 11,
    "internet_telecom": 13,
    "jobs_education": 958,
    "law_government": 19,
    "news": 16,
    "online_communities": 299,
    "people_society": 14,
    "pets_animals": 66,
    "real_estate": 29,
    "reference": 533,
    "science": 174,
    "shopping": 18,
    "sports": 20,
    "travel": 67,
}

# Time periods for validation
VALID_TIME_PERIODS = [
    "now 1-H",
    "now 4-H",
    "now 1-d",
    "now 7-d",
    "today 1-m",
    "today 3-m",
    "today 12-m",
    "today 5-y",
    "all",
]
