"""Event normalization and UID computation."""

from __future__ import annotations

from datetime import datetime

from utils.hashing import stable_hash
from utils.time import to_utc


def _parse_kickoff(kickoff_time: datetime | str) -> datetime:
    if isinstance(kickoff_time, datetime):
        return kickoff_time
    if isinstance(kickoff_time, str):
        value = kickoff_time.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    raise TypeError("kickoff_time must be datetime or ISO-8601 string")


def build_event_uid(
    league: str,
    home_team: str,
    away_team: str,
    kickoff_utc: datetime,
) -> str:
    payload = f"{league}|{home_team}|{away_team}|{kickoff_utc.isoformat()}"
    return stable_hash(payload)


def normalize_event(
    *,
    sport: str,
    league: str,
    season: str | None,
    home_team: str,
    away_team: str,
    kickoff_time: datetime | str,
    status: str,
    team_normalizer,
    league_normalizer,
) -> dict:
    league = league_normalizer.normalize(league)
    home_team = team_normalizer.normalize(home_team)
    away_team = team_normalizer.normalize(away_team)

    kickoff_raw = _parse_kickoff(kickoff_time)
    kickoff_utc = to_utc(kickoff_raw)

    event_uid = build_event_uid(
        league=league,
        home_team=home_team,
        away_team=away_team,
        kickoff_utc=kickoff_utc,
    )

    return {
        "event_uid": event_uid,
        "sport": sport,
        "league": league,
        "season": season,
        "home_team": home_team,
        "away_team": away_team,
        "kickoff_time": kickoff_utc,
        "status": status,
    }
