"""Immunefi signal source — Bug bounty and vulnerability data.

Immunefi is the leading bug bounty platform for Web3.
Free API: Public vulnerability disclosures.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class ImmunefiSource(SignalSource):
    """Fetches bug bounty and vulnerability data from Immunefi."""

    name = "immunefi"
    BASE_URL = "https://api.immunefi.com"
    RATE_LIMIT_PER_MINUTE = 10

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Poll Immunefi for bounty and vulnerability signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_bounties(),
            self._poll_vulnerabilities(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Immunefi poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_bounties(self) -> list[Signal]:
        """Fetch active bug bounties."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/v1/bounties")
            resp.raise_for_status()
            data = resp.json()

            for bounty in data.get("bounties", [])[:10]:
                reward = bounty.get("maxReward", 0)
                project = bounty.get("project", "Unknown")

                if reward > 100_000:  # >$100K bounties
                    signals.append(Signal(
                        source="immunefi",
                        signal_type=SignalType.VULNERABILITY,
                        title=f"Bug bounty: {project} (${reward/1e3:.0f}K)",
                        content=f"{project} has active bug bounty: up to ${reward/1e3:.0f}K",
                        url=f"https://immunefi.com/bounty/{project}",
                        topics=["Bug Bounty", project],
                        metadata={"project": project, "max_reward": reward},
                        confidence=0.9,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"Immunefi bounties failed: {e}")

        return signals

    async def _poll_vulnerabilities(self) -> list[Signal]:
        """Fetch recent vulnerability disclosures."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/v1/vulnerabilities")
            resp.raise_for_status()
            data = resp.json()

            for vuln in data.get("vulnerabilities", [])[:10]:
                project = vuln.get("project", "Unknown")
                severity = vuln.get("severity", "unknown")

                signals.append(Signal(
                    source="immunefi",
                    signal_type=SignalType.VULNERABILITY,
                    title=f"Vulnerability: {project} ({severity})",
                    content=f"{severity} vulnerability disclosed in {project}",
                    url=f"https://immunefi.com/vulnerability/{vuln.get('id', '')}",
                    topics=["Vulnerability", project, severity],
                    metadata={
                        "project": project,
                        "severity": severity,
                        "status": vuln.get("status", ""),
                    },
                    confidence=0.85,
                    urgency=8 if severity == "critical" else 6,
                ))

        except Exception as e:
            logger.warning(f"Immunefi vulnerabilities failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
