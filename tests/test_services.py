"""Tests for business logic services."""

from decimal import Decimal

import pytest

from app.utils.rate_matrix import RateMatrix


class TestRateMatrix:
    """Tests for RateMatrix utility class."""

    def test_get_rate_same_currency(self):
        """Test getting rate for same currency returns 1."""
        matrix = RateMatrix({"USD": Decimal("118.25")})
        rate = matrix.get_rate("USD", "USD")
        assert rate == Decimal("1")

    def test_get_rate_jpy_to_jpy(self):
        """Test JPY to JPY returns 1."""
        matrix = RateMatrix({"USD": Decimal("118.25")})
        rate = matrix.get_rate("JPY", "JPY")
        assert rate == Decimal("1")

    def test_get_rate_to_jpy(self):
        """Test getting rate to JPY."""
        matrix = RateMatrix({"USD": Decimal("118.25")})
        rate = matrix.get_rate("USD", "JPY")
        assert rate == Decimal("118.25")

    def test_get_rate_from_jpy(self):
        """Test getting rate from JPY."""
        matrix = RateMatrix({"USD": Decimal("118.25")})
        rate = matrix.get_rate("JPY", "USD")
        expected = (Decimal("1") / Decimal("118.25")).quantize(Decimal("0.0000000001"))
        assert rate == expected

    def test_get_rate_cross(self):
        """Test getting cross rate between two non-JPY currencies."""
        matrix = RateMatrix({
            "USD": Decimal("118.25"),
            "EUR": Decimal("128.50"),
        })
        rate = matrix.get_rate("EUR", "USD")
        expected = (Decimal("128.50") / Decimal("118.25")).quantize(Decimal("0.0000000001"))
        assert rate == expected

    def test_get_rate_unknown_currency(self):
        """Test getting rate for unknown currency returns None."""
        matrix = RateMatrix({"USD": Decimal("118.25")})
        rate = matrix.get_rate("UNKNOWN", "JPY")
        assert rate is None

    def test_convert_simple(self):
        """Test simple currency conversion."""
        matrix = RateMatrix({"USD": Decimal("118.25")})

        amount, rate = matrix.convert(Decimal("1000"), "JPY", "USD")

        assert amount is not None
        expected = (Decimal("1000") / Decimal("118.25")).quantize(Decimal("0.000001"))
        assert abs(amount - expected) < Decimal("0.01")

    def test_convert_unknown_currency(self):
        """Test conversion with unknown currency returns None."""
        matrix = RateMatrix({"USD": Decimal("118.25")})

        amount, rate = matrix.convert(Decimal("1000"), "UNKNOWN", "USD")

        assert amount is None
        assert rate is None

    def test_currencies_property(self):
        """Test currencies property returns all available currencies."""
        matrix = RateMatrix({
            "USD": Decimal("118.25"),
            "EUR": Decimal("128.50"),
        })

        currencies = matrix.currencies
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "JPY" in currencies  # Always included

    def test_get_all_rates(self):
        """Test get_all_rates returns copy of rates."""
        original_rates = {"USD": Decimal("118.25")}
        matrix = RateMatrix(original_rates)

        rates = matrix.get_all_rates()
        rates["USD"] = Decimal("200")  # Modify copy

        # Original should be unchanged
        assert matrix.get_rate("USD", "JPY") == Decimal("118.25")
