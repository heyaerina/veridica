"""Etherscan signal source — Token holders, transfers, contract data.

Etherscan provides Ethereum blockchain explorer data.
Free tier: 5 calls/sec, no key for basic endpoints.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class EtherscanSource(SignalSource):
    """Fetches token and contract data from Etherscan."""

    name = "etherscan"
    BASE_URL = "https://api.etherscan.io/api"
    RATE_LIMIT_PER_SECOND = 5

    def __init__(self, api_key: str = ""):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = api_key

    async def poll(self) -> list[Signal]:
        """Poll Etherscan for notable token transfers."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_large_transfers(),
            self._poll_new_tokens(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Etherscan poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_large_transfers(self) -> list[Signal]:
        """Detect large ERC-20 transfers."""
        signals = []
        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "address": "0x0000000000000000000000000000000000000000",
                "page": 1,
                "offset": 20,
                "sort": "desc",
            }
            if self.api_key:
                params["apikey"] = self.api_key

            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            for tx in data.get("result", []):
                value = int(tx.get("value", 0))
                decimals = int(tx.get("tokenDecimal", 18))
                symbol = tx.get("tokenSymbol", "Unknown")

                # Large transfers (>1M tokens assuming 18 decimals)
                if value > 1_000_000 * 10 ** decimals:
                    signals.append(Signal(
                        source="etherscan",
                        signal_type=SignalType.LARGE_TRANSFER,
                        title=f"Large transfer: {symbol}",
                        content=f"Large {symbol} transfer detected",
                        url=f"https://etherscan.io/tx/{tx.get('hash', '')}",
                        topics=["Transfer", symbol],
                        metadata={
                            "token": symbol,
                            "from": tx.get("from", ""),
                            "to": tx.get("to", ""),
                        },
                        confidence=0.8,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"Etherscan large transfers failed: {e}")

        return signals

    async def _poll_new_tokens(self) -> list[Signal]:
        """Detect newly created tokens."""
        signals = []
        try:
            params = {
                "module": "account",
                "action": "txlist",
                "address": "0x0000000000000000000000000000000000000000",
                "page": 1,
                "offset": 10,
                "sort": "desc",
            }
            if self.api_key:
                params["apikey"] = self.api_key

            resp = await self.client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            for tx in data.get("result", []):
                if tx.get("to") == "" and tx.get("input", "").startswith("0x60806040"):
                    signals.append(Signal(
                        source="etherscan",
                        signal_type=SignalType.NARRATIVE_EMERGENCE,
                        title="New contract deployed",
                        content=f"New contract creation detected",
                        url=f"https://etherscan.io/tx/{tx.get('hash', '')}",
                        topics=["Contract", "New"],
                        metadata={"tx_hash": tx.get("hash", "")},
                        confidence=0.5,
                        urgency=3,
                    ))

        except Exception as e:
            logger.warning(f"Etherscan new tokens failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
