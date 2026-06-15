"""Tally signal source — On-chain governance proposals.

Tally provides on-chain governance data for DAOs.
Free API: Public data.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class TallySource(SignalSource):
    """Fetches on-chain governance data from Tally."""

    name = "tally"
    BASE_URL = "https://api.tally.xyz"
    RATE_LIMIT_PER_MINUTE = 10

    def __init__(self, api_key: str = ""):
        self.client = httpx.AsyncClient(timeout=30.0)
        if api_key:
            self.client.headers["Api-Key"] = api_key

    async def poll(self) -> list[Signal]:
        """Poll Tally for governance proposals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_proposals(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Tally poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_proposals(self) -> list[Signal]:
        """Fetch active governance proposals."""
        signals = []
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/proposals",
                params={"state": "active", "limit": 20},
            )
            resp.raise_for_status()
            data = resp.json()

            for proposal in data.get("proposals", []):
                title = proposal.get("title", "Untitled")
                governor = proposal.get("governor", {}).get("name", "Unknown")
                votes = proposal.get("votesFor", 0) + proposal.get("votesAgainst", 0)

                signals.append(Signal(
                    source="tally",
                    signal_type=SignalType.DAO_PROPOSAL,
                    title=f"{governor}: {title[:50]}",
                    content=f"Active proposal on {governor}: {title}",
                    url=f"https://tally.xyz/proposal/{proposal.get('id', '')}",
                    topics=["Governance", governor],
                    metadata={
                        "governor": governor,
                        "votes_for": proposal.get("votesFor", 0),
                        "votes_against": proposal.get("votesAgainst", 0),
                    },
                    confidence=0.85,
                    urgency=6 if votes > 1_000_000 else 4,
                ))

        except Exception as e:
            logger.warning(f"Tally proposals failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
