from __future__ import annotations

from datetime import datetime, timezone

from db.models import Event
from normalization.events import normalize_event
from utils.logging import get_logger

logger = get_logger(__name__)


def _parse_iso_utc(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _split_teams(name: str) -> tuple[str, str] | None:
    if " v " in name:
        home, away = name.split(" v ", 1)
        return home.strip(), away.strip()
    return None


def ingest_events(session, adapter, team_normalizer, league_normalizer) -> None:
    raw_events = adapter.list_events()

    for ev in raw_events:
        provider_event_id = str(
            ev.get("id")
            or ev.get("event", {}).get("id")
            or ev.get("eventId")
            or ""
        )
        name = ev.get("name") or ev.get("event", {}).get("name") or ev.get("eventName") or ""
        open_date = (
            ev.get("openDate")
            or ev.get("event", {}).get("openDate")
            or ev.get("kickoff")
            or ev.get("startTime")
        )
        if not provider_event_id or not name or not open_date:
            continue

        teams = _split_teams(name)
        if not teams:
            continue
        home_raw, away_raw = teams

        try:
            home_team = team_normalizer.normalize(home_raw)
            away_team = team_normalizer.normalize(away_raw)
        except KeyError:
            continue

        league_raw = (
            ev.get("competition", {}).get("name")
            or ev.get("league")
            or ev.get("competitionName")
            or ""
        )
        if not league_raw:
            continue

        try:
            league = league_normalizer.normalize(league_raw)
        except KeyError:
            continue

        kickoff = _parse_iso_utc(str(open_date))

        event_data = normalize_event(
            sport="SOCCER",
            league=league,
            season=None,
            home_team=home_team,
            away_team=away_team,
            kickoff_time=kickoff,
            status="SCHEDULED",
            team_normalizer=team_normalizer,
            league_normalizer=league_normalizer,
        )

        existing = session.get(Event, event_data["event_uid"])
        if existing is None:
            existing = Event(**event_data)
            session.add(existing)

        if adapter.platform == "betfair":
            existing.betfair_id = provider_event_id
        elif adapter.platform == "betdex":
            existing.betdex_id = provider_event_id

    session.commit()
