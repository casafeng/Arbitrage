"""League name normalization."""

from typing import Dict


class LeagueNormalizer:
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
        self._validate_mapping()

    def _validate_mapping(self) -> None:
        reverse: dict[str, set[str]] = {}
        for alias, canonical in self.mapping.items():
            reverse.setdefault(alias, set()).add(canonical)

        for alias, canonicals in reverse.items():
            if len(canonicals) > 1:
                raise ValueError(
                    f"League alias '{alias}' maps to multiple canonicals: {canonicals}"
                )

    def normalize(self, league_name: str) -> str:
        try:
            return self.mapping[league_name]
        except KeyError as exc:
            raise KeyError(f"Unknown league alias: '{league_name}'") from exc
