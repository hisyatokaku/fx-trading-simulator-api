# DEMO_3DAY Scenario — Worked Example

A 3-day, 1-trade-per-day walkthrough of the FX simulation, run end-to-end
against a live server and verified against the API's own numbers. Use this
as a reference for how a session actually behaves, not just what the API
schema looks like.

## Scenario setup

| Field | Value |
|---|---|
| Name | `DEMO_3DAY` |
| Start | 2016-01-04 00:00:00 |
| End | 2016-01-07 00:00:00 |
| Interval | 86400s (1 day) |
| Starting balance | 1,000,000 JPY |

Defined in `data/scenarios.csv`. Each call to `/api/trade/next` executes
trades **at the current day's rate**, then advances one day. Because the
scenario spans exactly 3 intervals (Jan 4 → 5 → 6 → 7), it completes after
exactly 3 calls — one "trading day" each.

## Daily USD/EUR rates used

| Date | 1 USD = ? JPY | 1 EUR = ? JPY |
|---|---|---|
| 2016-01-04 (Day 1) | 118.25 | 128.50 |
| 2016-01-05 (Day 2) | 118.20 | 128.41 |
| 2016-01-06 (Day 3) | 118.11 | 128.30 |

## Day 1 — 2016-01-04

Starting balance: **1,000,000 JPY**, nothing else held.

Trade: convert **300,000 JPY → USD** at the day's rate (1 USD = 118.25 JPY).

```
amount_to = 300,000 × (1 / 118.25) = 2,536.99788 USD
```

**Balances after Day 1:** 700,000 JPY, 2,536.99788 USD
**Portfolio value:** 999,999.99931 JPY (essentially unchanged — the ~0.0007 JPY difference is just Decimal rounding on the conversion, not a real loss)

## Day 2 — 2016-01-05

Two trades this time — topping up the USD position and diversifying into EUR, since USD and EUR are at different rates today than yesterday.

Trade A: convert **200,000 JPY → USD** at today's rate (1 USD = 118.20 JPY, down slightly from 118.25):

```
amount_to = 200,000 × (1 / 118.20) = 1,692.04738 USD
```

Trade B: convert **150,000 JPY → EUR** at today's rate (1 EUR = 128.41 JPY):

```
amount_to = 150,000 × (1 / 128.41) = 1,168.133325 EUR
```

**Balances after Day 2:** 350,000 JPY, 4,229.04526 USD (2,536.99788 + 1,692.04738), 1,168.133325 EUR
**Portfolio value:** 999,873.149995 JPY

This is down about **126.85 JPY** from Day 1 — not from the new trades (which convert at the fair market rate, so they don't change portfolio value at the moment they happen), but because the **USD/JPY rate itself dipped** from 118.25 to 118.20 between Day 1 and Day 2, making the USD held since Day 1 worth marginally less in JPY terms.

## Day 3 — 2016-01-06

One trade: sell back **1,000 USD → JPY** at today's rate (1 USD = 118.11 JPY, down again from 118.20):

```
amount_to = 1,000 × 118.11 = 118,110 JPY
```

**Balances after Day 3:** 468,110 JPY (350,000 + 118,110), 3,229.04526 USD (4,229.04526 − 1,000), 1,168.133325 EUR (untouched)

The session's `current_datetime` advances to 2016-01-07, which equals `end_datetime` — **the session is now complete.**

## Final result

**Final portfolio value: 999,364.041256 JPY**

Starting from 1,000,000 JPY, the session ends about **636 JPY lower (−0.06%)**. This isn't a trading mistake — no trade was made at a bad rate relative to that day's market. It's simply the effect of holding open USD and EUR positions while the **USD/JPY rate drifted down across all three days (118.25 → 118.20 → 118.11)**: every day the unconverted USD/EUR balances were revalued at that day's rate, and the yen strengthened slightly against both, shrinking the JPY-equivalent value of the foreign-currency holdings.

## How this was run

Real calls against a live server (not hand-calculated):

```bash
curl -X POST $BASE/api/trade/start/DEMO_3DAY/<user_id>

curl -X POST $BASE/api/trade/next -d '{"session_id": <id>, "exchange_requests": [
  {"currency_from": "JPY", "currency_to": "USD", "amount": 300000}
]}'

curl -X POST $BASE/api/trade/next -d '{"session_id": <id>, "exchange_requests": [
  {"currency_from": "JPY", "currency_to": "USD", "amount": 200000},
  {"currency_from": "JPY", "currency_to": "EUR", "amount": 150000}
]}'

curl -X POST $BASE/api/trade/next -d '{"session_id": <id>, "exchange_requests": [
  {"currency_from": "USD", "currency_to": "JPY", "amount": 1000}
]}'
```

Every rate, converted amount, and balance above was verified independently against the API's own reported values (rate = fromRate/toRate to 10dp, amount = input × rate to 6dp, portfolio value = Σ balance × that day's rate) — no discrepancies found.
