"""Settings loader (env-based)."""

from dataclasses import dataclass
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

ENABLE_BETDEX = os.getenv("ENABLE_BETDEX", "0") == "1"
ENABLE_BETFAIR = os.getenv("ENABLE_BETFAIR", "0") == "1"
ENABLE_POLYMARKET = os.getenv("ENABLE_POLYMARKET", "0") == "1"
ENABLE_BETDEX_MOCK = os.getenv("ENABLE_BETDEX_MOCK", "0") == "1"
ENABLE_POLYMARKET_MOCK = os.getenv("ENABLE_POLYMARKET_MOCK", "0") == "1"


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            env=os.getenv("ARB_ENV", "local"),
            database_url=DATABASE_URL,
        )
