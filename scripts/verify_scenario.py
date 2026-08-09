#!/usr/bin/env python
"""
Run a full scenario end-to-end and verify all calculations are correct.

Usage:
    python scripts/verify_scenario.py [scenario] [user_id] [base_url]

Examples:
    python scripts/verify_scenario.py
    python scripts/verify_scenario.py DEMO_2016 testuser
    python scripts/verify_scenario.py DEMO_5MIN testuser http://localhost:8000
"""

import sys
import requests
from decimal import Decimal, ROUND_HALF_UP

BASE_URL  = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"
SCENARIO  = sys.argv[1] if len(sys.argv) > 1 else "DEMO_5MIN"
USER_ID   = sys.argv[2] if len(sys.argv) > 2 else "testuser"


def dec(v) -> Decimal:
    return Decimal(str(v))


def main():
    print(f"Scenario : {SCENARIO}")
    print(f"User     : {USER_ID}")
    print(f"Server   : {BASE_URL}")
    print()

    # ── Start session ─────────────────────────────────────────────────────────
    resp = requests.post(f"{BASE_URL}/api/trade/start/{SCENARIO}/{USER_ID}")
    if resp.status_code != 200:
        print(f"ERROR starting session: {resp.status_code} {resp.text}")
        sys.exit(1)

    session = resp.json()
    session_id = session["id"]
    print(f"Session {session_id} started: {session['current_datetime']} → {session['end_datetime']}")
    print(f"Initial balances: {session['balances']}\n")

    errors = []
    step = 0

    # ── Loop until complete ───────────────────────────────────────────────────
    while not session.get("is_complete"):
        step += 1

        # Simple repeating trade pattern to exercise buy and sell
        if step % 10 == 1:
            exchange_requests = [{"currency_from": "JPY", "currency_to": "USD", "amount": 50000}]
        elif step % 10 == 6:
            exchange_requests = [{"currency_from": "USD", "currency_to": "JPY", "amount": 100}]
        else:
            exchange_requests = []

        prev_balances = {k: dec(v) for k, v in session["balances"].items()}

        resp = requests.post(
            f"{BASE_URL}/api/trade/next",
            json={"session_id": session_id, "exchange_requests": exchange_requests},
        )
        if resp.status_code != 200:
            print(f"ERROR on step {step}: {resp.status_code} {resp.text}")
            sys.exit(1)

        result = resp.json()
        rates   = {k: dec(v) for k, v in result["rates"].items()}
        new_bal = {k: dec(v) for k, v in result["balances"].items()}
        trades  = result["trades"]

        # ── 1. Verify each trade ──────────────────────────────────────────────
        expected_balances = dict(prev_balances)
        for trade in trades:
            cfrom  = trade["currency_from"]
            cto    = trade["currency_to"]
            a_from = dec(trade["amount_from"])
            a_to   = dec(trade["amount_to"])
            rate   = dec(trade["rate"])

            # rate = from_jpy / to_jpy
            rate_from = rates.get(cfrom, Decimal("1"))
            rate_to   = rates.get(cto,   Decimal("1"))
            expected_rate = (rate_from / rate_to).quantize(
                Decimal("0.0000000001"), rounding=ROUND_HALF_UP
            )
            if abs(rate - expected_rate) > Decimal("0.000001"):
                errors.append(
                    f"Step {step}: rate mismatch {cfrom}→{cto}: got {rate}, expected {expected_rate}"
                )

            # amount_to = amount_from * rate (6 dp)
            expected_to = (a_from * rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            if abs(a_to - expected_to) > Decimal("0.0001"):
                errors.append(
                    f"Step {step}: amount_to mismatch: got {a_to}, expected {expected_to}"
                )

            expected_balances[cfrom] = expected_balances.get(cfrom, Decimal("0")) - a_from
            expected_balances[cto]   = expected_balances.get(cto,   Decimal("0")) + a_to

        # ── 2. Verify balances updated correctly ──────────────────────────────
        for currency, expected_amt in expected_balances.items():
            actual = new_bal.get(currency, Decimal("0"))
            if abs(actual - expected_amt) > Decimal("0.001"):
                errors.append(
                    f"Step {step}: balance mismatch {currency}: got {actual}, expected {expected_amt}"
                )

        # ── 3. Verify jpy_balance = Σ holding * rate_to_jpy ──────────────────
        if result["jpy_balance"] is not None:
            expected_jpy = sum(
                amt * rates.get(ccy, Decimal("1"))
                for ccy, amt in new_bal.items()
            ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            actual_jpy = dec(result["jpy_balance"])
            if abs(actual_jpy - expected_jpy) > Decimal("0.01"):
                errors.append(
                    f"Step {step}: jpy_balance mismatch: got {actual_jpy}, expected {expected_jpy}"
                )

        session = result

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"Completed after {step} steps")
    print(f"Final datetime  : {result['current_datetime']}")
    print(f"Final balances  : {result['balances']}")
    print(f"Final JPY total : {result['jpy_balance']}")
    print()

    if errors:
        print(f"FAIL — {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"PASS — all calculations verified correct across all {step} steps")


if __name__ == "__main__":
    main()
