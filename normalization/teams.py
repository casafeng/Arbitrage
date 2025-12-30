"""Team name normalization."""

from typing import Dict


class TeamNormalizer:
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
                    f"Alias '{alias}' maps to multiple canonicals: {canonicals}"
                )

    def normalize(self, team_name: str) -> str:
        try:
            return self.mapping[team_name]
        except KeyError as exc:
            raise KeyError(f"Unknown team alias: '{team_name}'") from exc
