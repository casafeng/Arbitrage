# arb-engine (Final Archive)

This system is validated in mock mode as a deterministic arbitrage research and audit engine. It ingests mock exchange markets and mock Polymarket markets, normalizes to a shared `event_uid`, computes worst-case P&L with fees and slippage, and persists accepted opportunities for audit.

## Validation Command
```bash
ENABLE_BETDEX=1 ENABLE_BETDEX_MOCK=1 ENABLE_POLYMARKET=1 ENABLE_POLYMARKET_MOCK=1 python main.py
```

## Interpreting the Arb Log Line
Example:
```
[arb] <event_uid> | Barcelona | PM_YES_vs_BDX_LAY | worst=EUR 0.89 | PM=0.400 | BDX_odds=1.700 | stake_pm=EUR 5.00 | hedge=EUR 2.99
```
Meaning:
- `PM_YES_vs_BDX_LAY` means buy YES on Polymarket and lay the same team on BetDEX.
- `PM=0.400` is the Polymarket YES price.
- `BDX_odds=1.700` is the BetDEX lay odds used in the hedge.
- `stake_pm` and `hedge` are the balanced stakes used in the worst-case P&L.
- `worst` is the minimum profit across outcomes after fees/slippage.

## What This System Is
This is a research/audit engine. It computes and persists evaluation results. It does not place or manage real orders.

## When Results Should NOT Be Trusted
- When any mock flag is enabled (`ENABLE_BETDEX_MOCK=1` or `ENABLE_POLYMARKET_MOCK=1`).
- When event or team normalization is incomplete or mismatched across sources.
- When exchange or prediction market data lacks required event fields (league, teams, kickoff).
- When fees, slippage, or commission assumptions are wrong for the venue.
# Arbitrage
