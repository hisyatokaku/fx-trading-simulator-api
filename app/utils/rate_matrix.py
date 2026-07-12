"""Rate matrix for currency conversions."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional


class RateMatrix:
    """Handles currency conversion using exchange rates to JPY."""

    def __init__(self, rates_to_jpy: Dict[str, Decimal]):
        self._rates = rates_to_jpy.copy()
        self._rates["JPY"] = Decimal("1")

    def get_rate(self, currency_from: str, currency_to: str) -> Optional[Decimal]:
        """Get exchange rate from one currency to another via JPY."""
        if currency_from not in self._rates or currency_to not in self._rates:
            return None

        rate_from_to_jpy = self._rates[currency_from]
        rate_to_to_jpy = self._rates[currency_to]

        if rate_to_to_jpy == Decimal("0"):
            return None

        return (rate_from_to_jpy / rate_to_to_jpy).quantize(
            Decimal("0.0000000001"), rounding=ROUND_HALF_UP
        )

    def convert(
        self,
        amount: Decimal,
        currency_from: str,
        currency_to: str,
    ) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """Convert amount from one currency to another.

        Returns:
            Tuple of (converted_amount, rate_used), or (None, None) if not possible.
        """
        rate = self.get_rate(currency_from, currency_to)
        if rate is None:
            return None, None

        converted = (amount * rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return converted, rate

    def get_all_rates(self) -> Dict[str, Decimal]:
        """Get all rates to JPY."""
        return self._rates.copy()

    @property
    def currencies(self) -> list[str]:
        """Get list of available currencies."""
        return list(self._rates.keys())
