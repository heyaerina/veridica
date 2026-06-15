"""DeFi Safety signal source — FREE protocol security scores.

DeFi Safety provides security ratings and audit status for DeFi protocols.
Free tier: Public API, no key required.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class DeFiSafetySource(SignalSource):
    """Fetches protocol security scores from DeFi Safety (free, no key)."""

    name = "defisafety"
    BASE_URL = "https://api.defisafety.com"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Veridica/2.0"},
        )

    async def poll(self) -> list[Signal]:
        """Poll DeFi Safety for protocol security signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_protocol_scores(),
            self._poll_recent_audits(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"DeFi Safety poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_protocol_scores(self) -> list[Signal]:
        """Fetch security scores for major protocols."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/protocols")
            if resp.status_code != 200:
                # Try alternative endpoint
                resp = await self.client.get(f"{self.BASE_URL}/api/v1/protocols")
            if resp.status_code != 200:
                return signals

            resp.raise_for_status()
            data = resp.json()
            protocols = data if isinstance(data, list) else data.get("protocols", data.get("data", []))

            for proto in protocols[:30]:
                name = proto.get("name", "")
                score = proto.get("score", proto.get("security_score", 0))
                chain = proto.get("chain", "")
                audit_status = proto.get("audit", proto.get("audited", False))

                # Flag protocols with low security scores
                if score and score < 50:
                    signals.append(Signal(
                        source="defisafety",
                        signal_type=SignalType.SECURITY_SCORE,
                        title=f"{name} security score: {score}/100",
                        content=f"{name} on {chain} has a low security score of {score}/100. "
                                f"Audited: {audit_status}",
                        url=f"https://defisafety.com/app/pq/{name.lower()}",
                        topics=[name, chain, "Security Score"],
                        metadata={
                            "protocol": name,
                            "chain": chain,
                            "score": score,
                            "audited": audit_status,
                        },
                        confidence=0.8,
                        urgency=6 if score < 30 else 4,
                    ))

                # Flag unaudited protocols with high TVL
                if audit_status is False and score and score > 70:
                    signals.append(Signal(
                        source="defisafety",
                        signal_type=SignalType.AUDIT_REPORT,
                        title=f"{name} unaudited despite high security score",
                        content=f"{name} has a security score of {score}/100 but is NOT audited. "
                                f"Community score may not reflect actual security.",
                        url=f"https://defisafety.com/app/pq/{name.lower()}",
                        topics=[name, "Audit", "Risk"],
                        metadata={
                            "protocol": name,
                            "chain": chain,
                            "score": score,
                        },
                        confidence=0.7,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"DeFi Safety protocol scores poll failed: {e}")

        return signals

    async def _poll_recent_audits(self) -> list[Signal]:
        """Check for recent audit reports."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/audits")
            if resp.status_code != 200:
                return signals

            resp.raise_for_status()
            data = resp.json()
            audits = data if isinstance(data, list) else data.get("audits", [])

            for audit in audits[:10]:
                protocol = audit.get("protocol", "")
                auditor = audit.get("auditor", "")
                date = audit.get("date", "")
                score = audit.get("score", 0)

                signals.append(Signal(
                    source="defisafety",
                    signal_type=SignalType.AUDIT_REPORT,
                    title=f"Audit: {protocol} by {auditor} - Score: {score}/100",
                    content=f"{protocol} was audited by {auditor}. "
                            f"Score: {score}/100. Date: {date}",
                    url=f"https://defisafety.com",
                    topics=[protocol, auditor, "Audit"],
                    metadata={
                        "protocol": protocol,
                        "auditor": auditor,
                        "date": date,
                        "score": score,
                    },
                    confidence=0.9,
                    urgency=3,
                ))

        except Exception as e:
            logger.warning(f"DeFi Safety audits poll failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
