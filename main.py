"""Entry point for the arbitrage engine."""

from config.loaders import load_league_normalizer, load_team_normalizer
from config.settings import (
    DATABASE_URL,
    ENABLE_BETDEX,
    ENABLE_BETFAIR,
    ENABLE_BETDEX_MOCK,
    ENABLE_POLYMARKET,
    ENABLE_POLYMARKET_MOCK,
)
from db.models import Event
from db.session import create_engine_and_session
from exchanges.betdex_adapter import BetDEXAdapter
from exchanges.betdex_mock_adapter import MockBetDEXAdapter
from exchanges.betfair_adapter import BetfairAdapter
from ingest.events import ingest_events
from ingest.exchange_markets import ingest_exchange_markets
from ingestion.betfair.client import BetfairClient
from ingestion.fixtures import load_fixtures
from ingestion.polymarket import PolymarketIngestor
from polymarket.client import PolymarketClient
from polymarket.mock_client import MockPolymarketClient
from arb_evaluator import evaluate_arbs
from utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting arb-engine")

    _engine, session_local = create_engine_and_session(DATABASE_URL)
    session = session_local()

    team_normalizer = load_team_normalizer()
    league_normalizer = load_league_normalizer()

    exchange = None
    if ENABLE_BETDEX:
        if ENABLE_BETDEX_MOCK:
            exchange = MockBetDEXAdapter()
        else:
            exchange = BetDEXAdapter(base_url="https://betdex.example")
    elif ENABLE_BETFAIR:
        bf_client = BetfairClient()
        exchange = BetfairAdapter(bf_client)

    if exchange:
        ingest_events(
            session=session,
            adapter=exchange,
            team_normalizer=team_normalizer,
            league_normalizer=league_normalizer,
        )
        event_rows = (
            session.query(Event)
            .filter(
                Event.betdex_id.isnot(None)
                if exchange.platform == "betdex"
                else Event.betfair_id.isnot(None)
            )
            .all()
        )
        ingest_exchange_markets(session, exchange, event_rows)
    else:
        fixtures = load_fixtures()

        for event_data in fixtures:
            exists = session.get(Event, event_data["event_uid"])
            if exists:
                logger.info("Event exists", extra={"event_uid": event_data["event_uid"]})
                continue

            event = Event(**event_data)
            session.add(event)
            logger.info("Inserted event", extra={"event_uid": event_data["event_uid"]})

        session.commit()

    if ENABLE_POLYMARKET:
        if ENABLE_POLYMARKET_MOCK:
            pm_client = MockPolymarketClient()
        else:
            pm_client = PolymarketClient()
        pm_ingestor = PolymarketIngestor(pm_client, team_normalizer, league_normalizer)
        pm_ingestor.ingest(session)

    results = evaluate_arbs(session)
    for result in results[:10]:
        print(
            f"[arb] {result.event_uid} | {result.team} | {result.direction} | "
            f"worst=EUR {result.worst_case_profit:.2f} | "
            f"PM={result.pm_price:.3f} | BDX_odds={result.bdx_odds:.3f} | "
            f"stake_pm=EUR {result.stake_pm:.2f} | "
            f"hedge=EUR {result.lay_stake_or_back_stake:.2f}"
        )
    session.close()

    logger.info("Startup complete")


if __name__ == "__main__":
    main()
