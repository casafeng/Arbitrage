from __future__ import annotations

from exchanges.base import ExchangeAdapter


class BetfairAdapter:
    platform = "betfair"

    def __init__(self, client):
        self.client = client

    def list_events(self) -> list[dict]:
        events: list[dict] = []
        competitions = self.client.list_competitions()
        for comp in competitions:
            comp_obj = comp.get("competition", {})
            comp_id = comp_obj.get("id") or comp.get("competitionId") or comp.get("id")
            if not comp_id:
                continue
            comp_name = comp_obj.get("name") or comp.get("competitionName")
            for ev in self.client.list_events(str(comp_id)):
                if comp_name:
                    ev = dict(ev)
                    ev["competition"] = ev.get("competition") or {"name": comp_name}
                events.append(ev)
        return events

    def list_markets(self, event_id: str) -> list[dict]:
        return self.client.list_markets(event_id)

    def list_market_book(self, market_id: str) -> dict:
        runners = self.client.list_runners(market_id)
        return {"market_id": market_id, "runners": runners}

    def place_order(self, order: dict) -> dict:
        raise NotImplementedError("Betfair execution not wired")
