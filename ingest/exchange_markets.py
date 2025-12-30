from __future__ import annotations

from datetime import datetime, timezone

from db.models import Event, ExchangeMarket


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pick_match_odds_market(markets: list[dict]) -> dict | None:
    for market in markets:
        name = (market.get("marketName") or market.get("name") or "").lower()
        mtype = (market.get("marketType") or market.get("type") or "").lower()
        if "match odds" in name or "full time result" in name or mtype in {
            "match_odds",
            "full_time_result",
        }:
            return market
    return markets[0] if markets else None


def ingest_exchange_markets(session, adapter, event_rows: list[Event]) -> None:
    for ev in event_rows:
        provider_event_id = (
            ev.betfair_id if adapter.platform == "betfair" else ev.betdex_id
        )
        if not provider_event_id:
            continue

        markets = adapter.list_markets(str(provider_event_id))
        market = _pick_match_odds_market(markets)
        if not market:
            continue

        market_id = str(
            market.get("marketId") or market.get("id") or market.get("market_id") or ""
        )
        if not market_id:
            continue

        market_name = market.get("marketName") or market.get("name")
        book = adapter.list_market_book(market_id)
        runners = book.get("runners") or book.get("selections") or []

        for runner in runners:
            selection_id = str(
                runner.get("selectionId")
                or runner.get("id")
                or runner.get("selection_id")
                or ""
            )
            selection_name = (
                runner.get("runnerName")
                or runner.get("name")
                or runner.get("selection_name")
                or ""
            )
            if not selection_id or not selection_name:
                continue

            back = runner.get("ex", {}).get("availableToBack") or runner.get("back") or []
            lay = runner.get("ex", {}).get("availableToLay") or runner.get("lay") or []

            best_back = float(back[0]["price"]) if back and "price" in back[0] else None
            best_lay = float(lay[0]["price"]) if lay and "price" in lay[0] else None

            row_id = f"{adapter.platform}:{market_id}:{selection_id}"
            row = session.query(ExchangeMarket).filter(ExchangeMarket.id == row_id).one_or_none()
            if row is None:
                row = ExchangeMarket(
                    id=row_id,
                    platform=adapter.platform,
                    event_uid=ev.event_uid,
                    market_id=market_id,
                    market_name=market_name,
                    selection_id=selection_id,
                    selection_name=selection_name,
                )
                session.add(row)

            row.best_back_odds = best_back
            row.best_lay_odds = best_lay
            row.last_updated = _utcnow()

    session.commit()
