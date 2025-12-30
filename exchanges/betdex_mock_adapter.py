from __future__ import annotations

from datetime import datetime, timezone


class MockBetDEXAdapter:
    platform = "betdex"

    def __init__(self) -> None:
        kickoff_1 = datetime(2025, 1, 10, 20, 0, tzinfo=timezone.utc).isoformat()
        kickoff_2 = datetime(2025, 1, 11, 18, 30, tzinfo=timezone.utc).isoformat()
        kickoff_3 = datetime(2025, 1, 12, 19, 0, tzinfo=timezone.utc).isoformat()
        self._events = [
            {
                "id": "mdx-1001",
                "name": "Chelsea v Bournemouth",
                "openDate": kickoff_1,
                "competition": {"name": "Premier League"},
            },
            {
                "id": "mdx-1002",
                "name": "Arsenal v Tottenham",
                "openDate": kickoff_2,
                "competition": {"name": "Premier League"},
            },
            {
                "id": "mdx-1003",
                "name": "Barcelona v Real Madrid",
                "openDate": kickoff_3,
                "competition": {"name": "La Liga"},
            },
        ]

        self._markets = {
            "mdx-1001": [
                {"marketId": "mkt-1001", "marketName": "Match Odds"},
            ],
            "mdx-1002": [
                {"marketId": "mkt-1002", "marketName": "Match Odds"},
            ],
            "mdx-1003": [
                {"marketId": "mkt-1003", "marketName": "Match Odds"},
            ],
        }

        self._books = {
            "mkt-1001": {
                "runners": [
                    {
                        "selectionId": "home",
                        "runnerName": "Chelsea",
                        # Case A: no arb (baseline)
                        "ex": {
                            "availableToBack": [{"price": 1.70, "size": 250.0}],
                            "availableToLay": [{"price": 1.76, "size": 200.0}],
                        },
                    },
                    {
                        "selectionId": "away",
                        "runnerName": "Bournemouth",
                        "ex": {
                            "availableToBack": [{"price": 5.50, "size": 90.0}],
                            "availableToLay": [{"price": 5.80, "size": 80.0}],
                        },
                    },
                    {
                        "selectionId": "draw",
                        "runnerName": "Draw",
                        "ex": {
                            "availableToBack": [{"price": 3.90, "size": 120.0}],
                            "availableToLay": [{"price": 4.10, "size": 100.0}],
                        },
                    },
                ]
            },
            "mkt-1002": {
                "runners": [
                    {
                        "selectionId": "home",
                        "runnerName": "Arsenal",
                        # Case B: marginal arb (killed by fees/slippage)
                        "ex": {
                            "availableToBack": [{"price": 2.05, "size": 180.0}],
                            "availableToLay": [{"price": 2.12, "size": 150.0}],
                        },
                    },
                    {
                        "selectionId": "away",
                        "runnerName": "Tottenham",
                        "ex": {
                            "availableToBack": [{"price": 3.40, "size": 110.0}],
                            "availableToLay": [{"price": 3.55, "size": 95.0}],
                        },
                    },
                    {
                        "selectionId": "draw",
                        "runnerName": "Draw",
                        "ex": {
                            "availableToBack": [{"price": 3.30, "size": 130.0}],
                            "availableToLay": [{"price": 3.45, "size": 120.0}],
                        },
                    },
                ]
            },
            "mkt-1003": {
                "runners": [
                    {
                        "selectionId": "home",
                        "runnerName": "Barcelona",
                        # Case C: clean arb (should pass)
                        "ex": {
                            "availableToBack": [{"price": 1.65, "size": 140.0}],
                            "availableToLay": [{"price": 1.70, "size": 130.0}],
                        },
                    },
                    {
                        "selectionId": "away",
                        "runnerName": "Real Madrid",
                        "ex": {
                            "availableToBack": [{"price": 2.80, "size": 150.0}],
                            "availableToLay": [{"price": 2.90, "size": 135.0}],
                        },
                    },
                    {
                        "selectionId": "draw",
                        "runnerName": "Draw",
                        "ex": {
                            "availableToBack": [{"price": 3.10, "size": 160.0}],
                            "availableToLay": [{"price": 3.25, "size": 150.0}],
                        },
                    },
                ]
            },
        }

    def list_events(self) -> list[dict]:
        return list(self._events)

    def list_markets(self, event_id: str) -> list[dict]:
        return list(self._markets.get(event_id, []))

    def list_market_book(self, market_id: str) -> dict:
        return dict(self._books.get(market_id, {"runners": []}))

    def place_order(self, order: dict) -> dict:
        raise NotImplementedError("Mock adapter is read-only")
