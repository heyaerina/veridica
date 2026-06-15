"""SlowMist Hacked signal source — FREE blockchain security incident database.

SlowMist maintains a comprehensive database of blockchain security incidents.
Data available via GitHub: https://github.com/nicoleahmed/SlowMist_Hacked
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class SlowMistSource(SignalSource):
    """Fetches security incident data from SlowMist (free, no key)."""

    name = "slowmist"
    # SlowMist Hacked GitHub raw data
    GITHUB_RAW = "https://raw.githubusercontent.com/nicoleahmed/SlowMist_Hacked/main"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Veridica/2.0"},
        )

    async def poll(self) -> list[Signal]:
        """Poll SlowMist for security incident signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_hacked_database(),
            self._poll_exploit_alerts(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"SlowMist poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_hacked_database(self) -> list[Signal]:
        """Fetch recent entries from SlowMist hacked database."""
        signals = []
        try:
            # Fetch the JSON database
            resp = await self.client.get(
                f"{self.GITHUB_RAW}/hacked.json"
            )
            if resp.status_code != 200:
                # Try alternative format
                resp = await self.client.get(
                    f"{self.GITHUB_RAW}/hacked_list.json"
                )
            if resp.status_code != 200:
                return signals

            resp.raise_for_status()
            data = resp.json()

            now = datetime.now()
            entries = data if isinstance(data, list) else data.get("entries", data.get("data", []))

            for entry in entries[:30]:
                date_str = entry.get("date", "")
                name = entry.get("name", entry.get("project", "Unknown"))
                chain = entry.get("chain", entry.get("blockchain", "Unknown"))
                amount = entry.get("amount", entry.get("funds_lost", 0))
                attack_type = entry.get("type", entry.get("attack_type", "unknown"))

                try:
                    if isinstance(date_str, str):
                        incident_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        continue
                    days_ago = (now - incident_date).days
                except (ValueError, TypeError):
                    continue

                if 0 <= days_ago <= 7:
                    # Parse amount if string
                    if isinstance(amount, str):
                        amount = amount.replace("$", "").replace(",", "")
                        try:
                            amount = float(amount)
                        except ValueError:
                            amount = 0

                    signals.append(Signal(
                        source="slowmist",
                        signal_type=SignalType.SECURITY_INCIDENT,
                        title=f"[SlowMist] {name} exploited: ${amount/1e6:.1f}M lost on {chain}",
                        content=f"{name} was exploited for ${amount/1e6:.1f}M on {chain}. "
                                f"Attack type: {attack_type}. "
                                f"Reported {days_ago} days ago.",
                        url="https://slowmist-hacked.github.io/",
                        topics=[name, chain, "Exploit", attack_type],
                        metadata={
                            "protocol": name,
                            "chain": chain,
                            "amount": amount,
                            "attack_type": attack_type,
                            "days_ago": days_ago,
                        },
                        confidence=0.95,
                        urgency=9 if amount > 1_000_000 else 8,
                    ))

        except Exception as e:
            logger.warning(f"SlowMist hacked database poll failed: {e}")

        return signals

    async def _poll_exploit_alerts(self) -> list[Signal]:
        """Check for active exploit alerts."""
        signals = []
        try:
            # Check SlowMist Twitter/X feed or alert system
            resp = await self.client.get("https://slowmist.com/api/alerts")
            if resp.status_code != 200:
                return signals

            resp.raise_for_status()
            alerts = resp.json()

            for alert in alerts[:5]:
                signals.append(Signal(
                    source="slowmist",
                    signal_type=SignalType.VULNERABILITY,
                    title=f"[SlowMist Alert] {alert.get('title', 'Security Alert')}",
                    content=alert.get("description", ""),
                    url=alert.get("url", "https://slowmist.com"),
                    topics=["Security Alert", alert.get("category", "")],
                    metadata=alert,
                    confidence=0.85,
                    urgency=8,
                ))

        except Exception as e:
            logger.warning(f"SlowMist alerts poll failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
