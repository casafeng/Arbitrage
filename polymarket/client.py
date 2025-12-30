"""Minimal Polymarket client wrapper."""

from __future__ import annotations

import json
import os
from typing import Iterable

import requests

from utils.logging import get_logger

logger = get_logger(__name__)


class PolymarketClient:
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        self.session.headers.update({"Accept": "application/json"})

    def get_markets(self, *, limit: int = 200) -> list[dict]:
        markets: list[dict] = []
        offset = 0
        seen_ids: set[str] = set()

        while True:
            resp = self.session.get(
                f"{self.BASE_URL}/markets",
                params={"limit": limit, "offset": offset},
                timeout=10,
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break

            normalized = self._normalize_batch(batch)
            for item in normalized:
                market_id = item.get("id")
                if market_id and market_id in seen_ids:
                    continue
                if market_id:
                    seen_ids.add(market_id)
                markets.append(item)

            if len(batch) < limit:
                break
            if len(seen_ids) == len(markets) and len(markets) > 0 and len(batch) == limit and offset > 0:
                # Offset appears ineffective; avoid infinite pagination loop.
                break
            offset += limit

        logger.info("Fetched Polymarket markets", extra={"count": len(markets)})
        return markets

    def _normalize_batch(self, batch: Iterable[dict]) -> list[dict]:
        normalized = []
        for market in batch:
            normalized.append(self._normalize_market(market))
        return normalized

    def _normalize_market(self, market: dict) -> dict:
        outcomes = _parse_json_list(market.get("outcomes"))
        prices = _parse_json_list(market.get("outcomePrices"))

        yes_price = None
        if outcomes and prices and len(outcomes) == len(prices):
            for outcome, price in zip(outcomes, prices):
                if str(outcome).lower() == "yes":
                    try:
                        yes_price = float(price)
                    except (TypeError, ValueError):
                        yes_price = None
                    break

        first_event = None
        events = market.get("events")
        if isinstance(events, list) and events:
            first_event = events[0]

        kickoff = None
        if isinstance(first_event, dict):
            kickoff = first_event.get("startDate") or first_event.get("endDate")

        return {
            "id": market.get("id"),
            "question": market.get("question"),
            "price": yes_price,
            "liquidity": _safe_float(market.get("liquidityNum") or market.get("liquidity")),
            "league": market.get("league") or (first_event.get("league") if first_event else None),
            "team": market.get("team") or market.get("team_name"),
            "home_team": market.get("home_team") or market.get("homeTeam"),
            "away_team": market.get("away_team") or market.get("awayTeam"),
            "kickoff": kickoff,
            "category": market.get("category") or (first_event.get("category") if first_event else None),
            "outcomeType": "BINARY" if outcomes and [o.lower() for o in outcomes] == ["yes", "no"] else None,
        }


def _parse_json_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
