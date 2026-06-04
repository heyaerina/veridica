"""DeFiLlama signal source — FREE on-chain data API."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class DeFiLlamaSource(SignalSource):
    """Fetches on-chain intelligence from DeFiLlama (100% free, no API key)."""

    name = "defillama"
    BASE_URL = "https://api.llama.fi"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Poll all DeFiLlama endpoints for signals."""
        signals: list[Signal] = []

        # Run all polls concurrently
        import asyncio
        results = await asyncio.gather(
            self._poll_tvl_changes(),
            self._poll_stablecoins(),
            self._poll_trending(),
            self._poll_new_protocols(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"DeFiLlama poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_tvl_changes(self) -> list[Signal]:
        """Detect protocols with significant TVL changes."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/protocols")
            resp.raise_for_status()
            protocols = resp.json()

            for proto in protocols[:50]:  # Top 50 protocols
                name = proto.get("name", "Unknown")
                tvl = proto.get("tvl", 0)
                change_1d = proto.get("change_1d", 0)
                change_7d = proto.get("change_7d", 0)
                chain = proto.get("chain", "Multi-chain")
                category = proto.get("category", "Unknown")
                url = proto.get("url", "")

                # Significant TVL change (>15% in 1 day)
                if change_1d and abs(change_1d) > 15:
                    urgency = 8 if abs(change_1d) > 30 else 6
                    direction = "surged" if change_1d > 0 else "dumped"

                    signals.append(Signal(
                        source="defillama",
                        signal_type=SignalType.TVL_CHANGE,
                        title=f"{name} TVL {direction} {abs(change_1d):.1f}% in 24h",
                        content=(
                            f"{name} ({chain}) TVL {direction} from "
                            f"${tvl/1e6:.1f}M. Category: {category}. "
                            f"7d change: {change_7d:+.1f}%"
                        ),
                        url=url,
                        topics=self._extract_topics(name, category, chain),
                        metadata={
                            "protocol": name,
                            "tvl": tvl,
                            "change_1d": change_1d,
                            "change_7d": change_7d,
                            "chain": chain,
                            "category": category,
                        },
                        confidence=0.9,
                        urgency=urgency,
                    ))

        except Exception as e:
            logger.warning(f"DeFiLlama TVL poll failed: {e}")

        return signals

    async def _poll_stablecoins(self) -> list[Signal]:
        """Detect stablecoin depegs."""
        signals = []
        try:
            # DeFiLlama stablecoins endpoint
            resp = await self.client.get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
            resp.raise_for_status()
            data = resp.json()
            stables = data.get("peggedAssets", [])

            for stable in stables[:20]:  # Top 20 stablecoins
                name = stable.get("name", "Unknown")
                symbol = stable.get("symbol", "")
                price = stable.get("price", 1.0)
                circulating = stable.get("circulating", {}).get("peggedUSD", 0)

                if not price or not circulating:
                    continue

                # Detect depeg (>1% deviation from $1)
                deviation = abs(price - 1.0)
                if deviation > 0.01:
                    urgency = 9 if deviation > 0.05 else 7
                    direction = "above" if price > 1 else "below"

                    signals.append(Signal(
                        source="defillama",
                        signal_type=SignalType.DEPEG,
                        title=f"{name} ({symbol}) depegged: ${price:.4f}",
                        content=(
                            f"{name} is trading at ${price:.4f}, "
                            f"{deviation*100:.2f}% {direction} peg. "
                            f"Circulating supply: ${circulating/1e6:.0f}M"
                        ),
                        topics=["Stablecoin", "Depeg", symbol],
                        metadata={
                            "stablecoin": name,
                            "symbol": symbol,
                            "price": price,
                            "deviation": deviation,
                            "circulating": circulating,
                        },
                        confidence=0.95,
                        urgency=urgency,
                    ))

        except Exception as e:
            logger.warning(f"DeFiLlama stablecoin poll failed: {e}")

        return signals

    async def _poll_trending(self) -> list[Signal]:
        """Get trending protocols by fees/revenue."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
            resp.raise_for_status()
            data = resp.json()
            protocols = data.get("protocols", [])

            # Top protocols by daily fees
            for proto in protocols[:10]:
                name = proto.get("name", "Unknown")
                daily_fees = proto.get("total24h", 0)
                daily_revenue = proto.get("totalAllTime", 0)

                if daily_fees and daily_fees > 100000:  # >$100K daily fees
                    signals.append(Signal(
                        source="defillama",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"{name} generating ${daily_fees/1e3:.0f}K daily fees",
                        content=f"{name} daily fees: ${daily_fees/1e3:.0f}K",
                        topics=self._extract_topics(name, "", ""),
                        metadata={
                            "protocol": name,
                            "daily_fees": daily_fees,
                        },
                        confidence=0.8,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"DeFiLlama trending poll failed: {e}")

        return signals

    async def _poll_new_protocols(self) -> list[Signal]:
        """Detect recently added protocols."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/protocols")
            resp.raise_for_status()
            protocols = resp.json()

            # Find protocols with very recent listings (listed within 7 days)
            now = datetime.now()
            for proto in protocols:
                listed_at = proto.get("listedAt")
                if listed_at:
                    listed_date = datetime.fromtimestamp(listed_at)
                    days_since = (now - listed_date).days
                    if 0 <= days_since <= 7:
                        name = proto.get("name", "Unknown")
                        tvl = proto.get("tvl", 0)
                        chain = proto.get("chain", "Multi-chain")
                        category = proto.get("category", "Unknown")

                        if tvl and tvl > 1_000_000:  # >$1M TVL
                            signals.append(Signal(
                                source="defillama",
                                signal_type=SignalType.NEW_PROTOCOL,
                                title=f"New protocol: {name} ({chain}) with ${tvl/1e6:.1f}M TVL",
                                content=(
                                    f"{name} just listed on DeFiLlama. "
                                    f"Chain: {chain}. Category: {category}. "
                                    f"TVL: ${tvl/1e6:.1f}M"
                                ),
                                topics=self._extract_topics(name, category, chain),
                                metadata={
                                    "protocol": name,
                                    "tvl": tvl,
                                    "chain": chain,
                                    "category": category,
                                    "listed_days_ago": days_since,
                                },
                                confidence=0.85,
                                urgency=6,
                            ))

        except Exception as e:
            logger.warning(f"DeFiLlama new protocols poll failed: {e}")

        return signals

    def _extract_topics(self, name: str, category: str, chain: str) -> list[str]:
        """Extract topics from protocol data."""
        topics = []
        if name:
            topics.append(name)
        if category:
            topics.append(category)
        if chain and chain != "Multi-chain":
            topics.append(chain)
        return topics

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
