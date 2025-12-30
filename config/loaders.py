"""Config loaders for normalization tables."""

import json
from pathlib import Path

from normalization.leagues import LeagueNormalizer
from normalization.teams import TeamNormalizer

BASE_DIR = Path(__file__).resolve().parent


def load_team_normalizer() -> TeamNormalizer:
    path = BASE_DIR / "teams.json"
    with open(path, "r", encoding="utf-8") as handle:
        mapping = json.load(handle)
    return TeamNormalizer(mapping)


def load_league_normalizer() -> LeagueNormalizer:
    path = BASE_DIR / "leagues.json"
    with open(path, "r", encoding="utf-8") as handle:
        mapping = json.load(handle)
    return LeagueNormalizer(mapping)
