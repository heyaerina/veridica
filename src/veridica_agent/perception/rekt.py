"""Rekt.news signal source — FREE exploit/hack tracking.

Rekt.news is the leading crypto exploit database.
Scrapes public JSON feed for latest hacks, exploits, and rug pulls.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class RektSource(SignalSource):
    """Fetches exploit and hack data from Rekt.news (free, no key)."""

    name = "rekt"
    BASE_URL = "https://rekt.news"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Veridica/2.0"},
        )

    async def poll(self) -> list[Signal]:
        """Poll Rekt.news for exploit signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_leaderboard(),
            self._poll_recent_incidents(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Rekt.news poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_leaderboard(self) -> list[Signal]:
        """Check Rekt leaderboard for recent major exploits."""
        signals = []
        try:
            # Rekt leaderboard JSON
            resp = await self.client.get(f"{self.BASE_URL}/leaderboard.json")
            if resp.status_code != 200:
                # Fallback: try scraping main page
                return await self._scrape_main_page()
            resp.raise_for_status()
            data = resp.json()

            now = datetime.now()
            for entry in data[:20]:
                funds_lost = entry.get("fundsLost", 0)
                date_str = entry.get("date", "")
                name = entry.get("name", "Unknown Protocol")
                chain = entry.get("chain", "Unknown")
                exploit_type = entry.get("type", "unknown")

                if not funds_lost or not date_str:
                    continue

                try:
                    incident_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    days_ago = (now - incident_date).days
                except (ValueError, TypeError):
                    continue

                # Only recent incidents (last 7 days)
                if 0 <= days_ago <= 7:
                    signals.append(Signal(
                        source="rekt",
                        signal_type=SignalType.EXPLOIT,
                        title=f"REKT: {name} lost ${funds_lost/1e6:.1f}M on {chain}",
                        content=f"{name} was exploited for ${funds_lost/1e6:.1f}M. "
                                f"Chain: {chain}. Type: {exploit_type}. "
                                f"Days ago: {days_ago}",
                        url=f"https://rekt.news",
                        topics=[name, chain, "Exploit", "Security"],
                        metadata={
                            "protocol": name,
                            "chain": chain,
                            "funds_lost": funds_lost,
                            "exploit_type": exploit_type,
                            "days_ago": days_ago,
                        },
                        confidence=0.95,
                        urgency=9 if funds_lost > 10_000_000 else 8,
                    ))

        except Exception as e:
            logger.warning(f"Rekt leaderboard poll failed: {e}")

        return signals

    async def _poll_recent_incidents(self) -> list[Signal]:
        """Fetch recent incident reports."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/incidents.json")
            if resp.status_code != 200:
                return signals
            resp.raise_for_status()
            incidents = resp.json()

            now = datetime.now()
            for incident in incidents[:10]:
                date_str = incident.get("date", "")
                name = incident.get("name", "")
                amount = incident.get("amount", 0)
                chain = incident.get("chain", "")
                category = incident.get("category", "")

                try:
                    incident_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    days_ago = (now - incident_date).days
                except (ValueError, TypeError):
                    continue

                if 0 <= days_ago <= 3:  # Very recent
                    signals.append(Signal(
                        source="rekt",
                        signal_type=SignalType.SECURITY_INCIDENT,
                        title=f"Security incident: {name} ({chain})",
                        content=f"Recent security incident on {name}. "
                                f"Chain: {chain}. Category: {category}. "
                                f"Amount: ${amount/1e6:.1f}M",
                        url=f"https://rekt.news",
                        topics=[name, chain, "Security", category],
                        metadata={
                            "protocol": name,
                            "chain": chain,
                            "amount": amount,
                            "category": category,
                            "days_ago": days_ago,
                        },
                        confidence=0.9,
                        urgency=9,
                    ))

        except Exception as e:
            logger.warning(f"Rekt incidents poll failed: {e}")

        return signals

    async def _scrape_main_page(self) -> list[Signal]:
        """Fallback: scrape main rekt.news page."""
        return []

    async def close(self):
        await self.client.aclose()
