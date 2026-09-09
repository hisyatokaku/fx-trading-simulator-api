"""The currencies the simulator supports.

Rates for any other currency that happen to be in the rates table (e.g. CNY
left over from old demo data) are ignored: they are never returned by the
rate endpoints and can never be traded.
"""

SUPPORTED_CURRENCIES = [
    "JPY", "USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF",
    "TRY", "ZAR", "MXN", "NOK", "SEK", "HKD",
]
