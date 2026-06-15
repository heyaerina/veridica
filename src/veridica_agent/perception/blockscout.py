"""Blockscout signal source — Contract verification and token transfers.

Blockscout is an open-source blockchain explorer.
Free API: No key required for public instances.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class BlockscoutSource(SignalSource):
    """Fetches contract and token data from Blockscout."""

    name = "blockscout"
    BASE_URL = "https://eth.blockscout.com/api/v2"
    RATE_LIMIT_PER_MINUTE = 30

    def __init__(self, base_url: str = ""):
        self.client = httpx.AsyncClient(timeout=30.0)
        if base_url:
            self.BASE_URL = base_url

    async def poll(self) -> list[Signal]:
        """Poll Blockscout for notable token transfers and contracts."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_token_transfers(),
            self._poll_new_contracts(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Blockscout poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_token_transfers(self) -> list[Signal]:
        """Detect large token transfers."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/token-transfers")
            resp.raise_for_status()
            data = resp.json()

            for transfer in data.get("items", [])[:20]:
                value = float(transfer.get("total", {}).get("value", 0))
                token = transfer.get("token", {}).get("symbol", "Unknown")

                if value > 1_000_000:  # >$1M
                    signals.append(Signal(
                        source="blockscout",
                        signal_type=SignalType.LARGE_TRANSFER,
                        title=f"Token transfer: {value:,.0f} {token}",
                        content=f"Large {token} transfer detected on chain",
                        url=f"https://eth.blockscout.com/tx/{transfer.get('tx_hash', '')}",
                        topics=["Transfer", token],
                        metadata={"token": token, "value": value},
                        confidence=0.85,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"Blockscout token transfers failed: {e}")

        return signals

    async def _poll_new_contracts(self) -> list[Signal]:
        """Detect notable new verified contracts."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/smart-contracts")
            resp.raise_for_status()
            data = resp.json()

            for contract in data.get("items", [])[:10]:
                if contract.get("is_verified"):
                    name = contract.get("name", "Unknown")
                    signals.append(Signal(
                        source="blockscout",
                        signal_type=SignalType.NARRATIVE_EMERGENCE,
                        title=f"New verified contract: {name}",
                        content=f"Verified smart contract deployed: {name}",
                        url=f"https://eth.blockscout.com/address/{contract.get('address', '')}",
                        topics=["Contract", name],
                        metadata={"address": contract.get("address", ""), "name": name},
                        confidence=0.6,
                        urgency=4,
                    ))

        except Exception as e:
            logger.warning(f"Blockscout new contracts failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
