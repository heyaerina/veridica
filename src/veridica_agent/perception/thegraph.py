"""The Graph signal source — Indexed blockchain data via subgraphs.

The Graph provides indexed blockchain data via GraphQL.
Free tier: 100K queries/month.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class TheGraphSource(SignalSource):
    """Fetches indexed blockchain data from The Graph."""

    name = "thegraph"
    RATE_LIMIT_PER_MINUTE = 60

    # Popular subgraphs
    SUBGRAPHS = {
        "uniswap_v3": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "aave_v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
    }

    def __init__(self, api_key: str = ""):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = api_key
        # Gateway URL if API key provided
        if api_key:
            self.gateway = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id"
        else:
            self.gateway = ""

    async def poll(self) -> list[Signal]:
        """Poll The Graph for DEX and protocol data."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_uniswap_volume(),
            self._poll_aave_health(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"The Graph poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_uniswap_volume(self) -> list[Signal]:
        """Fetch Uniswap V3 daily volume."""
        signals = []
        try:
            query = """
            {
              pools(first: 5, orderBy: volumeUSD, orderDirection: desc) {
                token0 { symbol }
                token1 { symbol }
                volumeUSD
                totalValueLockedUSD
              }
            }
            """
            url = self.SUBGRAPHS["uniswap_v3"]
            resp = await self.client.post(url, json={"query": query})
            resp.raise_for_status()
            data = resp.json()

            for pool in data.get("data", {}).get("pools", []):
                volume = float(pool.get("volumeUSD", 0))
                tvl = float(pool.get("totalValueLockedUSD", 0))
                pair = f"{pool['token0']['symbol']}/{pool['token1']['symbol']}"

                if volume > 100_000_000:  # >$100M volume
                    signals.append(Signal(
                        source="thegraph",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"Uniswap: {pair} ${volume/1e6:.0f}M vol",
                        content=f"{pair}: ${volume/1e6:.0f}M volume, ${tvl/1e6:.1f}M TVL",
                        url="https://app.uniswap.org",
                        topics=["Uniswap", "DEX", pair],
                        metadata={"pair": pair, "volume": volume, "tvl": tvl},
                        confidence=0.9,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"The Graph Uniswap failed: {e}")

        return signals

    async def _poll_aave_health(self) -> list[Signal]:
        """Fetch Aave protocol health metrics."""
        signals = []
        try:
            query = """
            {
              markets(first: 5) {
                name
                totalValueLockedUSD
                totalBorrowBalanceUSD
              }
            }
            """
            url = self.SUBGRAPHS["aave_v3"]
            resp = await self.client.post(url, json={"query": query})
            resp.raise_for_status()
            data = resp.json()

            for market in data.get("data", {}).get("markets", []):
                tvl = float(market.get("totalValueLockedUSD", 0))
                borrows = float(market.get("totalBorrowBalanceUSD", 0))
                name = market.get("name", "Unknown")

                if tvl > 1_000_000_000:  # >$1B TVL
                    utilization = borrows / tvl if tvl > 0 else 0
                    signals.append(Signal(
                        source="thegraph",
                        signal_type=SignalType.PROTOCOL_SCORE,
                        title=f"Aave: {name} ${tvl/1e9:.1f}B TVL",
                        content=f"{name}: ${tvl/1e9:.1f}B TVL, {utilization:.1%} utilization",
                        url="https://app.aave.com",
                        topics=["Aave", "Lending", name],
                        metadata={"name": name, "tvl": tvl, "utilization": utilization},
                        confidence=0.9,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"The Graph Aave failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
