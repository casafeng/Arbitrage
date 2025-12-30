from __future__ import annotations

import requests


class BetDEXAdapter:
    platform = "betdex"

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.session.headers.update({"Accept": "application/json"})

    def list_events(self) -> list[dict]:
        resp = self.session.get(f"{self.base_url}/events", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def list_markets(self, event_id: str) -> list[dict]:
        resp = self.session.get(f"{self.base_url}/events/{event_id}/markets", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def list_market_book(self, market_id: str) -> dict:
        resp = self.session.get(f"{self.base_url}/markets/{market_id}/book", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def place_order(self, order: dict) -> dict:
        raise NotImplementedError("Execution later")
