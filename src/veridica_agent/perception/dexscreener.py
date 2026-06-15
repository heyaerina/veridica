"""DEXScreener signal source — DEX pair data and trending tokens.

DEXScreener provides real-time DEX trading data.
Free API: No key required.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class DEXScreenerSource(SignalSource):
    """Fetches DEX pair data from DEXScreener."""

    name = "dexscreener"
    BASE_URL = "https://api.dexscreener.com/latest"
    RATE_LIMIT_PER_MINUTE = 30

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Poll DEXScreener for trending pairs and new listings."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_trending(),
            self._poll_new_pairs(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"DEXScreener poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_trending(self) -> list[Signal]:
        """Fetch trending DEX pairs."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/dex/tokens/trending")
            resp.raise_for_status()
            data = resp.json()

            for pair in data.get("pairs", [])[:10]:
                volume_24h = pair.get("volume", {}).get("h24", 0)
                price_change = pair.get("priceChange", {}).get("h24", 0)
                token = pair.get("baseToken", {}).get("symbol", "Unknown")
                dex = pair.get("dexId", "Unknown")

                if volume_24h > 1_000_000:  # >$1M volume
                    signals.append(Signal(
                        source="dexscreener",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"Trending: {token} ${volume_24h/1e6:.1f}M vol",
                        content=f"{token} on {dex}: ${volume_24h/1e6:.1f}M volume, {price_change:+.1f}% 24h",
                        url=pair.get("url", "https://dexscreener.com"),
                        topics=["DEX", token, dex],
                        metadata={
                            "token": token,
                            "dex": dex,
                            "volume_24h": volume_24h,
                            "price_change_24h": price_change,
                        },
                        confidence=0.8,
                        urgency=7 if abs(price_change) > 50 else 5,
                    ))

        except Exception as e:
            logger.warning(f"DEXScreener trending failed: {e}")

        return signals

    async def _poll_new_pairs(self) -> list[Signal]:
        """Fetch newly created DEX pairs."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/dex/pairs/boosted")
            resp.raise_for_status()
            data = resp.json()

            for pair in data.get("pairs", [])[:10]:
                token = pair.get("baseToken", {}).get("symbol", "Unknown")
                dex = pair.get("dexId", "Unknown")
                liquidity = pair.get("liquidity", {}).get("usd", 0)

                if liquidity > 100_000:  # >$100K liquidity
                    signals.append(Signal(
                        source="dexscreener",
                        signal_type=SignalType.NARRATIVE_EMERGENCE,
                        title=f"New pair: {token} on {dex}",
                        content=f"New boosted pair: {token} with ${liquidity/1e3:.0f}K liquidity on {dex}",
                        url=pair.get("url", "https://dexscreener.com"),
                        topics=["New Pair", token, dex],
                        metadata={
                            "token": token,
                            "dex": dex,
                            "liquidity": liquidity,
                        },
                        confidence=0.6,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"DEXScreener new pairs failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
