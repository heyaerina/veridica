"""DeFiLlama Yields signal source — Yield farming data.

Extends DeFiLlama with yield pool data.
Free API: No key required.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class DeFiLlamaYieldsSource(SignalSource):
    """Fetches yield farming data from DeFiLlama."""

    name = "defillama_yields"
    BASE_URL = "https://yields.llama.fi"
    RATE_LIMIT_PER_MINUTE = 30

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Poll DeFiLlama for yield opportunities and changes."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_high_yields(),
            self._poll_yield_changes(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"DeFiLlama Yields poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_high_yields(self) -> list[Signal]:
        """Detect unusually high yield opportunities."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/pools")
            resp.raise_for_status()
            data = resp.json()

            for pool in data.get("data", [])[:100]:
                apy = pool.get("apy", 0)
                tvl = pool.get("tvlUsd", 0)
                project = pool.get("project", "Unknown")
                symbol = pool.get("symbol", "")

                # High APY with decent TVL
                if apy > 50 and tvl > 1_000_000:
                    signals.append(Signal(
                        source="defillama_yields",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"High yield: {symbol} {apy:.1f}% APY",
                        content=f"{project}: {symbol} offering {apy:.1f}% APY with ${tvl/1e6:.1f}M TVL",
                        url=f"https://defillama.com/yields/pool/{pool.get('pool', '')}",
                        topics=["Yield", project, symbol],
                        metadata={
                            "project": project,
                            "symbol": symbol,
                            "apy": apy,
                            "tvl": tvl,
                        },
                        confidence=0.7,
                        urgency=6 if apy > 100 else 4,
                    ))

        except Exception as e:
            logger.warning(f"DeFiLlama high yields failed: {e}")

        return signals

    async def _poll_yield_changes(self) -> list[Signal]:
        """Detect significant yield changes."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/pools")
            resp.raise_for_status()
            data = resp.json()

            for pool in data.get("data", [])[:100]:
                apy_change = pool.get("apyMean30d", 0) - pool.get("apy", 0)
                project = pool.get("project", "Unknown")
                symbol = pool.get("symbol", "")

                # Significant yield drop
                if apy_change > 20:  # >20% drop
                    signals.append(Signal(
                        source="defillama_yields",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"Yield drop: {symbol} -{apy_change:.1f}%",
                        content=f"{project}: {symbol} APY dropped {apy_change:.1f}%",
                        url=f"https://defillama.com/yields/pool/{pool.get('pool', '')}",
                        topics=["Yield", project, symbol],
                        metadata={
                            "project": project,
                            "symbol": symbol,
                            "apy_change": apy_change,
                        },
                        confidence=0.75,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"DeFiLlama yield changes failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
