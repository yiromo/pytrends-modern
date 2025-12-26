"""
Unit tests for pytrends-modern
"""

import pytest
import pandas as pd
from datetime import date

from pytrends_modern import TrendReq, TrendsRSS
from pytrends_modern.exceptions import (
    InvalidParameterError,
    ResponseError,
    TooManyRequestsError,
)
from pytrends_modern.utils import (
    convert_dates_to_timeframe,
    validate_keywords,
    normalize_geo_code,
)


class TestTrendReq:
    """Tests for TrendReq class"""

    def test_initialization(self):
        """Test TrendReq initialization"""
        pytrends = TrendReq(hl="en-US", tz=360)
        assert pytrends.hl == "en-US"
        assert pytrends.tz == 360
        assert isinstance(pytrends.kw_list, list)

    def test_build_payload_valid(self):
        """Test build_payload with valid parameters"""
        pytrends = TrendReq()
        pytrends.build_payload(["Python"], timeframe="today 12-m")
        assert pytrends.kw_list == ["Python"]

    def test_build_payload_too_many_keywords(self):
        """Test build_payload with too many keywords"""
        pytrends = TrendReq()
        with pytest.raises(ValueError):
            pytrends.build_payload(["k1", "k2", "k3", "k4", "k5", "k6"], timeframe="today 12-m")

    def test_build_payload_no_keywords(self):
        """Test build_payload with no keywords"""
        pytrends = TrendReq()
        with pytest.raises(ValueError):
            pytrends.build_payload([], timeframe="today 12-m")

    def test_build_payload_invalid_gprop(self):
        """Test build_payload with invalid gprop"""
        pytrends = TrendReq()
        with pytest.raises(ValueError):
            pytrends.build_payload(["Python"], gprop="invalid")

    @pytest.mark.integration
    def test_interest_over_time(self):
        """Integration test for interest_over_time"""
        pytrends = TrendReq()
        pytrends.build_payload(["Python"], timeframe="now 7-d")
        df = pytrends.interest_over_time()

        assert isinstance(df, pd.DataFrame)
        assert "Python" in df.columns
        assert "isPartial" in df.columns

    @pytest.mark.integration
    def test_suggestions(self):
        """Integration test for suggestions"""
        pytrends = TrendReq()
        suggestions = pytrends.suggestions("python")

        assert isinstance(suggestions, list)
        if suggestions:
            assert "title" in suggestions[0]


class TestTrendsRSS:
    """Tests for TrendsRSS class"""

    def test_initialization(self):
        """Test TrendsRSS initialization"""
        rss = TrendsRSS(timeout=15)
        assert rss.timeout == 15

    def test_validate_geo_valid(self):
        """Test geo validation with valid codes"""
        rss = TrendsRSS()
        assert rss._validate_geo("us") == "US"
        assert rss._validate_geo("GB") == "GB"
        assert rss._validate_geo("us-ca") == "US-CA"

    def test_validate_geo_invalid(self):
        """Test geo validation with invalid code"""
        rss = TrendsRSS()
        with pytest.raises(InvalidParameterError):
            rss._validate_geo("INVALID")

    @pytest.mark.integration
    def test_get_trends(self):
        """Integration test for get_trends"""
        rss = TrendsRSS()
        trends = rss.get_trends(geo="US", output_format="dict")

        assert isinstance(trends, list)
        if trends:
            assert "title" in trends[0]
            assert "traffic" in trends[0]

    @pytest.mark.integration
    def test_get_trends_dataframe(self):
        """Integration test for get_trends with DataFrame output"""
        rss = TrendsRSS()
        df = rss.get_trends(geo="US", output_format="dataframe")

        assert isinstance(df, pd.DataFrame)
        assert "title" in df.columns

    def test_get_available_geos(self):
        """Test get_available_geos"""
        rss = TrendsRSS()
        geos = rss.get_available_geos()

        assert isinstance(geos, dict)
        assert "US" in geos
        assert "GB" in geos
        assert "US-CA" in geos


class TestUtils:
    """Tests for utility functions"""

    def test_convert_dates_to_timeframe(self):
        """Test date to timeframe conversion"""
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)
        timeframe = convert_dates_to_timeframe(start, end)

        assert timeframe == "2023-01-01 2023-12-31"

    def test_validate_keywords_valid(self):
        """Test keyword validation with valid input"""
        assert validate_keywords(["Python", "JavaScript"]) is True

    def test_validate_keywords_empty(self):
        """Test keyword validation with empty list"""
        with pytest.raises(ValueError):
            validate_keywords([])

    def test_validate_keywords_too_many(self):
        """Test keyword validation with too many keywords"""
        with pytest.raises(ValueError):
            validate_keywords(["k1", "k2", "k3", "k4", "k5", "k6"])

    def test_validate_keywords_empty_string(self):
        """Test keyword validation with empty string"""
        with pytest.raises(ValueError):
            validate_keywords([""])

    def test_normalize_geo_code(self):
        """Test geo code normalization"""
        assert normalize_geo_code("us") == "US"
        assert normalize_geo_code("GB") == "GB"
        assert normalize_geo_code("us-ca") == "US-CA"


class TestExceptions:
    """Tests for custom exceptions"""

    def test_response_error(self):
        """Test ResponseError"""
        error = ResponseError("Test error")
        assert str(error) == "Test error"

    def test_invalid_parameter_error(self):
        """Test InvalidParameterError"""
        error = InvalidParameterError("Invalid param")
        assert str(error) == "Invalid param"


# Pytest configuration
@pytest.fixture
def sample_dataframe():
    """Fixture providing sample trend data"""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    data = {"Python": range(50, 60), "JavaScript": range(60, 70), "isPartial": [False] * 10}
    return pd.DataFrame(data, index=dates)


def test_sample_dataframe(sample_dataframe):
    """Test the sample dataframe fixture"""
    assert isinstance(sample_dataframe, pd.DataFrame)
    assert "Python" in sample_dataframe.columns
    assert len(sample_dataframe) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
