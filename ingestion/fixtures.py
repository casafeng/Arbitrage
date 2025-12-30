"""Fixtures ingestion to create canonical events."""

from config.loaders import load_league_normalizer, load_team_normalizer
from normalization.events import normalize_event


def load_fixtures() -> list[dict]:
    team_normalizer = load_team_normalizer()
    league_normalizer = load_league_normalizer()

    raw_fixtures = [
        {
            "sport": "SOCCER",
            "league": "Premier League",
            "season": "2025/26",
            "home_team": "Chelsea FC",
            "away_team": "BOU",
            "kickoff_time": "2025-12-30T20:30:00Z",
            "status": "SCHEDULED",
        }
    ]

    events: list[dict] = []

    for raw in raw_fixtures:
        event = normalize_event(
            sport=raw["sport"],
            league=raw["league"],
            season=raw["season"],
            home_team=raw["home_team"],
            away_team=raw["away_team"],
            kickoff_time=raw["kickoff_time"],
            status=raw["status"],
            team_normalizer=team_normalizer,
            league_normalizer=league_normalizer,
        )
        events.append(event)

    return events
