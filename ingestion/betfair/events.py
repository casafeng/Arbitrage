"""Betfair events ingestion."""

from db.models import Event
from normalization.events import normalize_event
from utils.logging import get_logger

logger = get_logger(__name__)


def ingest_events(session, client, team_normalizer, league_normalizer) -> None:
    competitions = client.list_competitions()

    for comp in competitions:
        comp_id = comp["competition"]["id"]
        raw_league = comp["competition"]["name"]

        try:
            league = league_normalizer.normalize(raw_league)
        except KeyError:
            continue

        events = client.list_events(comp_id)

        for item in events:
            raw_event = item["event"]
            raw_name = raw_event["name"]

            try:
                home_team, away_team = raw_name.split(" v ")
            except ValueError:
                logger.warning("Unparsable event name", extra={"name": raw_name})
                continue

            try:
                home_team = team_normalizer.normalize(home_team)
                away_team = team_normalizer.normalize(away_team)
            except KeyError:
                continue

            kickoff = raw_event["openDate"].replace("Z", "+00:00")

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
            if existing:
                existing.betfair_id = raw_event["id"]
                continue

            event = Event(**event_data, betfair_id=raw_event["id"])
            session.add(event)
            logger.info(
                "Inserted Betfair event",
                extra={"home_team": home_team, "away_team": away_team, "kickoff": kickoff},
            )

    session.commit()
