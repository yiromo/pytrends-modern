"""
Tests configuration and fixtures
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_interest_over_time_df():
    """
    Sample DataFrame mimicking interest_over_time() output
    """
    dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
    data = {"Python": range(40, 70), "JavaScript": range(50, 80), "isPartial": [False] * 30}
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    return df


@pytest.fixture
def sample_interest_by_region_df():
    """
    Sample DataFrame mimicking interest_by_region() output
    """
    regions = ["California", "Texas", "New York", "Florida", "Illinois"]
    data = {"Python": [100, 85, 90, 75, 80]}
    df = pd.DataFrame(data, index=regions)
    df.index.name = "geoName"
    return df


@pytest.fixture
def sample_related_queries():
    """
    Sample related queries structure
    """
    return {
        "Python": {
            "top": pd.DataFrame(
                {
                    "query": ["python tutorial", "python download", "python programming"],
                    "value": [100, 85, 75],
                }
            ),
            "rising": pd.DataFrame(
                {
                    "query": ["python 3.12", "python ai", "python machine learning"],
                    "value": ["Breakout", "+500%", "+300%"],
                }
            ),
        }
    }


@pytest.fixture
def sample_rss_trends():
    """
    Sample RSS trends data
    """
    return [
        {
            "title": "Breaking News: Tech Event",
            "description": "Major tech announcement",
            "link": "https://example.com/news1",
            "pub_date": "Mon, 26 Dec 2025 12:00:00 +0000",
            "traffic": 500000,
            "picture": "https://example.com/image1.jpg",
            "articles": [
                {
                    "title": "Article 1",
                    "url": "https://example.com/article1",
                    "snippet": "Article snippet...",
                    "source": "Tech News",
                }
            ],
            "article_count": 1,
        },
        {
            "title": "Sports Update",
            "description": "Championship game results",
            "link": "https://example.com/sports1",
            "pub_date": "Mon, 26 Dec 2025 11:00:00 +0000",
            "traffic": 300000,
            "picture": "https://example.com/image2.jpg",
            "articles": [],
            "article_count": 0,
        },
    ]


@pytest.fixture
def mock_google_trends_response():
    """
    Mock response structure from Google Trends API
    """
    return {
        "default": {
            "timelineData": [
                {"time": "1640995200", "value": [50], "isPartial": [False]},
                {"time": "1641081600", "value": [55], "isPartial": [False]},
                {"time": "1641168000", "value": [60], "isPartial": [False]},
            ]
        }
    }


# Pytest markers
def pytest_configure(config):
    """
    Configure custom pytest markers
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires network)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Test collection
def pytest_collection_modifyitems(config, items):
    """
    Automatically skip integration tests unless --integration flag is used
    """
    if not config.getoption("--integration", default=False):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """
    Add custom command line options
    """
    parser.addoption(
        "--integration", action="store_true", default=False, help="run integration tests"
    )
