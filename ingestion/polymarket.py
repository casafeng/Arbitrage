"""Polymarket ingestion for binary soccer markets."""

from collections import Counter
from datetime import datetime, timezone

from db.models import BinaryMarket, Event
from normalization.events import build_event_uid
from utils.logging import get_logger
from utils.time import to_utc

logger = get_logger(__name__)

SKIP_NOT_SPORTS = "not_sports"
SKIP_NOT_BINARY = "not_binary"
SKIP_NO_EVENT_FIELDS = "missing_event_fields"
SKIP_NO_MATCHING_EVENT = "no_matching_event"
SKIP_UNKNOWN_TEAM = "unknown_team"
SKIP_UNKNOWN_LEAGUE = "unknown_league"
SKIP_OTHER = "other_error"


class PolymarketIngestor:
    def __init__(self, client, team_normalizer, league_normalizer):
        self.client = client
        self.team_norm = team_normalizer
        self.league_norm = league_normalizer
        self.stats = Counter()
        self.missing_field_stats = Counter()

    def ingest(self, session) -> None:
        markets = self.client.get_markets()

        for market in markets:
            try:
                self._process_market(session, market)
            except Exception as exc:
                self.stats[SKIP_OTHER] += 1

        session.commit()
        self._log_stats(len(markets))

    def _process_market(self, session, raw: dict) -> None:
        if raw.get("category") != "Sports":
            self.stats[SKIP_NOT_SPORTS] += 1
            return

        if raw.get("outcomeType") != "BINARY":
            self.stats[SKIP_NOT_BINARY] += 1
            return

        question = raw.get("question", "")
        if "win" not in question.lower():
            return

        required_fields = ["league", "home_team", "away_team", "kickoff"]
        missing = []
        for key in required_fields:
            if key not in raw:
                missing.append(key)
                continue
            value = raw.get(key)
            if value is None:
                missing.append(key)
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(key)

        if missing:
            self.stats[SKIP_NO_EVENT_FIELDS] += 1
            for field in missing:
                self.missing_field_stats[field] += 1
            return

        try:
            league = self.league_norm.normalize(raw["league"])
        except KeyError:
            self.stats[SKIP_UNKNOWN_LEAGUE] += 1
            return

        try:
            team = self.team_norm.normalize(raw["team"])
            home_team = self.team_norm.normalize(raw["home_team"])
            away_team = self.team_norm.normalize(raw["away_team"])
        except KeyError:
            self.stats[SKIP_UNKNOWN_TEAM] += 1
            return

        kickoff_value = raw["kickoff"].replace("Z", "+00:00")
        kickoff_dt = datetime.fromisoformat(kickoff_value)
        kickoff_utc = to_utc(kickoff_dt)

        event_uid = build_event_uid(
            league=league,
            home_team=home_team,
            away_team=away_team,
            kickoff_utc=kickoff_utc,
        )

        event = session.get(Event, event_uid)
        if not event:
            self.stats[SKIP_NO_MATCHING_EVENT] += 1
            return

        existing = (
            session.query(BinaryMarket)
            .filter_by(platform="polymarket", market_id=raw["id"])
            .one_or_none()
        )

        if existing:
            existing.price = raw["price"]
            existing.liquidity = raw.get("liquidity")
            existing.last_updated = datetime.now(timezone.utc)
            return

        market = BinaryMarket(
            platform="polymarket",
            market_id=raw["id"],
            event_uid=event_uid,
            team=team,
            question=question,
            yes_means=f"{team} wins the match",
            no_means=f"{team} does not win (draw or lose)",
            price=raw["price"],
            liquidity=raw.get("liquidity"),
            last_updated=datetime.now(timezone.utc),
        )

        session.add(market)

    def _log_stats(self, total: int) -> None:
        ingested = total - sum(self.stats.values())
        logger.info(
            "Polymarket ingestion summary",
            extra={
                "total": total,
                "ingested": ingested,
                "skips": dict(self.stats),
            },
        )
        if self.missing_field_stats:
            most_common = self.missing_field_stats.most_common(3)
            logger.info(
                "Most missing event fields: "
                + ", ".join(f"{field}={count}" for field, count in most_common)
            )
