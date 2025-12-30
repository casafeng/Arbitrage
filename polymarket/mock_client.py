from __future__ import annotations


class MockPolymarketClient:
    def __init__(self) -> None:
        self._markets = [
            {
                "id": "pm-2001",
                "question": "Will Chelsea win?",
                # Case A: no arb (baseline)
                "price": 0.56,
                "liquidity": 5000.0,
                "league": "Premier League",
                "team": "Chelsea",
                "home_team": "Chelsea",
                "away_team": "Bournemouth",
                "kickoff": "2025-01-10T20:00:00+00:00",
                "category": "Sports",
                "outcomeType": "BINARY",
            },
            {
                "id": "pm-2002",
                "question": "Will Arsenal win?",
                # Case B: marginal arb (killed by fees/slippage)
                "price": 0.45,
                "liquidity": 4000.0,
                "league": "Premier League",
                "team": "Arsenal",
                "home_team": "Arsenal",
                "away_team": "Tottenham",
                "kickoff": "2025-01-11T18:30:00+00:00",
                "category": "Sports",
                "outcomeType": "BINARY",
            },
            {
                "id": "pm-2003",
                "question": "Will Barcelona win?",
                # Case C: clean arb (should pass)
                "price": 0.40,
                "liquidity": 3500.0,
                "league": "La Liga",
                "team": "Barcelona",
                "home_team": "Barcelona",
                "away_team": "Real Madrid",
                "kickoff": "2025-01-12T19:00:00+00:00",
                "category": "Sports",
                "outcomeType": "BINARY",
            },
        ]

    def get_markets(self) -> list[dict]:
        return list(self._markets)
