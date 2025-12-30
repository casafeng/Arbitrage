from __future__ import annotations

from typing import Protocol


class ExchangeAdapter(Protocol):
    platform: str

    def list_events(self) -> list[dict]:
        """Return provider events."""
        ...

    def list_markets(self, event_id: str) -> list[dict]:
        """Return markets for an event."""
        ...

    def list_market_book(self, market_id: str) -> dict:
        """Return market book snapshot for a market."""
        ...

    def place_order(self, order: dict) -> dict:
        """Optional execution entry point."""
        raise NotImplementedError
