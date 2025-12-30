"""Minimal Betfair client wrapper."""

from __future__ import annotations

import os
import requests

from utils.logging import get_logger

logger = get_logger(__name__)


class BetfairClient:
    IDENTITY_URL = "https://identitysso-cert.betfair.com/api/certlogin"
    API_URL = "https://api.betfair.com/exchange/betting/json-rpc/v1"

    def __init__(self):
        self.app_key = os.getenv("BETFAIR_APP_KEY")
        self.username = os.getenv("BETFAIR_USERNAME")
        self.password = os.getenv("BETFAIR_PASSWORD")
        self.cert = (
            os.getenv("BETFAIR_CERT_CRT"),
            os.getenv("BETFAIR_CERT_KEY"),
        )

        if not all([self.app_key, self.username, self.password, *self.cert]):
            raise RuntimeError("Missing Betfair credentials")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Application": self.app_key,
                "Content-Type": "application/json",
            }
        )

        self._login()

    def _login(self) -> None:
        resp = self.session.post(
            self.IDENTITY_URL,
            data={"username": self.username, "password": self.password},
            cert=self.cert,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("loginStatus") != "SUCCESS":
            raise RuntimeError(f"Betfair login failed: {data}")

        token = data["sessionToken"]
        self.session.headers.update({"X-Authentication": token})
        logger.info("Betfair login successful")

    def _rpc(self, method: str, params: dict) -> list[dict]:
        payload = [
            {
                "jsonrpc": "2.0",
                "method": f"SportsAPING/v1.0/{method}",
                "params": params,
                "id": 1,
            }
        ]

        resp = self.session.post(
            self.API_URL,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()[0]

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["result"]

    def list_competitions(self) -> list[dict]:
        return self._rpc(
            "listCompetitions",
            {
                "filter": {
                    "eventTypeIds": ["1"],
                }
            },
        )

    def list_events(self, competition_id: str) -> list[dict]:
        return self._rpc(
            "listEvents",
            {
                "filter": {
                    "competitionIds": [competition_id],
                }
            },
        )

    def list_markets(self, event_id: str) -> list[dict]:
        return self._rpc(
            "listMarketCatalogue",
            {
                "filter": {
                    "eventIds": [event_id],
                    "marketTypeCodes": ["MATCH_ODDS"],
                },
                "maxResults": 10,
                "marketProjection": ["EVENT"],
            },
        )

    def list_runners(self, market_id: str) -> list[dict]:
        return self._rpc(
            "listMarketBook",
            {
                "marketIds": [market_id],
                "priceProjection": {
                    "priceData": ["EX_BEST_OFFERS"],
                },
            },
        )
