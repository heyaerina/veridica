"""Dune Analytics signal source — On-chain analytics.

Dune provides community SQL queries on blockchain data.
API: https://api.dune.com/api/v1
Free tier: 1000 API credits/month with API key.
MCP endpoint: https://api.dune.com/mcp/v1
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class DuneSource(SignalSource):
    """Fetches on-chain analytics from Dune Analytics."""

    name = "dune"
    BASE_URL = "https://api.dune.com/api/v1"
    MCP_URL = "https://api.dune.com/mcp/v1"

    # Free tier: 1000 credits/month ≈ ~33/day if polled daily
    RATE_LIMIT_PER_DAY = 30  # Conservative to stay within monthly budget

    def __init__(self, api_key: str = ""):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.api_key = api_key
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Dune-API-Key"] = api_key
        self.client.headers.update(headers)

        # Rate limit tracking
        self._requests_today: list[float] = []

    async def poll(self) -> list[Signal]:
        """Poll Dune for on-chain intelligence signals."""
        signals: list[Signal] = []

        if not self.api_key:
            logger.debug("Dune: no API key, skipping")
            return signals

        import asyncio
        results = await asyncio.gather(
            self._poll_whale_movements(),
            self._poll_protocol_metrics(),
            self._poll_stablecoin_flows(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Dune poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _execute_query(self, query_id: int, limit: int = 100) -> list[dict]:
        """Execute a Dune query and return results."""
        try:
            # Execute query
            resp = await self.client.post(
                f"{self.BASE_URL}/query/{query_id}/execute",
                json={"performance": "medium"},
            )
            resp.raise_for_status()
            execution = resp.json()
            execution_id = execution.get("execution_id")

            if not execution_id:
                logger.warning(f"Dune: no execution_id for query {query_id}")
                return []

            # Poll for results (max 30s)
            import asyncio
            for _ in range(6):
                await asyncio.sleep(5)
                resp = await self.client.get(
                    f"{self.BASE_URL}/execution/{execution_id}/results"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("result", {}).get("rows", [])

            logger.warning(f"Dune: query {query_id} timed out")
            return []

        except Exception as e:
            logger.warning(f"Dune query {query_id} failed: {e}")
            return []

    async def _poll_whale_movements(self) -> list[Signal]:
        """Detect large token transfers using Dune community queries."""
        signals = []
        try:
            # Query 3584032: Large ETH transfers
            rows = await self._execute_query(3584032)
            for row in rows[:10]:
                amount = row.get("amount", 0)
                if amount > 1000:  # >1000 ETH
                    signals.append(Signal(
                        source="dune",
                        signal_type=SignalType.WHALE_MOVEMENT,
                        title=f"Whale moved {amount:,.0f} ETH",
                        content=f"Large ETH transfer detected: {amount:,.0f} ETH. "
                                f"From: {str(row.get('from', 'unknown'))[:10]}... "
                                f"To: {str(row.get('to', 'unknown'))[:10]}...",
                        url="https://dune.com",
                        topics=["Ethereum", "Whale", "Large Transfer"],
                        metadata={
                            "chain": "ethereum",
                            "amount": amount,
                            "from": row.get("from", ""),
                            "to": row.get("to", ""),
                        },
                        confidence=0.9,
                        urgency=8 if amount > 10000 else 6,
                    ))

        except Exception as e:
            logger.warning(f"Dune whale movement poll failed: {e}")

        return signals

    async def _poll_protocol_metrics(self) -> list[Signal]:
        """Fetch protocol TVL and volume metrics from Dune."""
        signals = []
        try:
            # Query 2748926: DEX volume daily
            rows = await self._execute_query(2748926)
            for row in rows[:5]:
                volume = row.get("volume", 0)
                if volume > 100_000_000:  # >$100M daily volume
                    signals.append(Signal(
                        source="dune",
                        signal_type=SignalType.VOLUME_SPIKE,
                        title=f"DEX volume spike: ${volume/1e6:.0f}M",
                        content=f"Daily DEX volume: ${volume/1e6:.0f}M",
                        url="https://dune.com",
                        topics=["DEX", "Volume"],
                        metadata={"volume": volume},
                        confidence=0.85,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"Dune protocol metrics poll failed: {e}")

        return signals

    async def _poll_stablecoin_flows(self) -> list[Signal]:
        """Monitor stablecoin mint/burn events."""
        signals = []
        try:
            # Query 299960: Stablecoin supply changes
            rows = await self._execute_query(299960)
            for row in rows[:5]:
                change = row.get("supply_change", 0)
                if abs(change) > 50_000_000:  # >$50M change
                    direction = "minted" if change > 0 else "burned"
                    signals.append(Signal(
                        source="dune",
                        signal_type=SignalType.LARGE_TRANSFER,
                        title=f"Stablecoin {direction}: ${abs(change)/1e6:.0f}M",
                        content=f"{row.get('symbol', 'Unknown')} {direction} "
                                f"${abs(change)/1e6:.0f}M in 24h",
                        url="https://dune.com",
                        topics=["Stablecoin", row.get("symbol", "")],
                        metadata={
                            "symbol": row.get("symbol", ""),
                            "change": change,
                        },
                        confidence=0.9,
                        urgency=7 if abs(change) > 100_000_000 else 5,
                    ))

        except Exception as e:
            logger.warning(f"Dune stablecoin flows poll failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
