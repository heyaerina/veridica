"""CoinGecko signal source — FREE market data API."""

from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class CoinGeckoSource(SignalSource):
    """Fetches market intelligence from CoinGecko (free tier, no API key)."""

    name = "coingecko"
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Poll CoinGecko for market signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_trending(),
            self._poll_top_movers(),
            self._poll_global_stats(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"CoinGecko poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_trending(self) -> list[Signal]:
        """Get trending coins — what people are searching for."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/search/trending")
            resp.raise_for_status()
            data = resp.json()
            coins = data.get("coins", [])

            for item in coins[:7]:
                coin = item.get("item", {})
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "")
                market_cap_rank = coin.get("market_cap_rank")
                price_btc = coin.get("price_btc", 0)

                signals.append(Signal(
                    source="coingecko",
                    signal_type=SignalType.TRENDING,
                    title=f"Trending: {name} ({symbol})",
                    content=(
                        f"{name} is trending on CoinGecko. "
                        f"Symbol: {symbol}. "
                        f"MCap rank: #{market_cap_rank if market_cap_rank else 'N/A'}. "
                        f"Price BTC: {price_btc:.8f}"
                    ),
                    topics=["Trending", symbol, name],
                    metadata={
                        "name": name,
                        "symbol": symbol,
                        "market_cap_rank": market_cap_rank,
                        "price_btc": price_btc,
                    },
                    confidence=0.7,
                    urgency=6,
                ))

        except Exception as e:
            logger.warning(f"CoinGecko trending poll failed: {e}")

        return signals

    async def _poll_top_movers(self) -> list[Signal]:
        """Detect coins with biggest price movements."""
        signals = []
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 50,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h",
                },
            )
            resp.raise_for_status()
            coins = resp.json()

            for coin in coins:
                name = coin.get("name", "Unknown")
                symbol = coin.get("symbol", "").upper()
                price = coin.get("current_price", 0)
                change_24h = coin.get("price_change_percentage_24h", 0)
                volume = coin.get("total_volume", 0)
                market_cap = coin.get("market_cap", 0)

                if not change_24h:
                    continue

                # Significant price movement (>10% in 24h)
                if abs(change_24h) > 10:
                    urgency = 8 if abs(change_24h) > 20 else 6
                    direction = "pumped" if change_24h > 0 else "dumped"

                    signals.append(Signal(
                        source="coingecko",
                        signal_type=SignalType.PRICE_MOVEMENT,
                        title=f"{symbol} {direction} {abs(change_24h):.1f}% in 24h",
                        content=(
                            f"{name} ({symbol}) {direction} {abs(change_24h):.1f}% "
                            f"in 24h. Price: ${price:.4f}. "
                            f"Volume: ${volume/1e6:.1f}M. "
                            f"Market cap: ${market_cap/1e6:.0f}M"
                        ),
                        topics=[symbol, name, "Price Movement"],
                        metadata={
                            "name": name,
                            "symbol": symbol,
                            "price": price,
                            "change_24h": change_24h,
                            "volume": volume,
                            "market_cap": market_cap,
                        },
                        confidence=0.85,
                        urgency=urgency,
                    ))

                # Volume spike (volume > 50% of market cap = unusual)
                if market_cap > 0 and volume > 0:
                    volume_ratio = volume / market_cap
                    if volume_ratio > 0.5:
                        signals.append(Signal(
                            source="coingecko",
                            signal_type=SignalType.VOLUME_SPIKE,
                            title=f"{symbol} unusual volume: {volume_ratio*100:.0f}% of mcap",
                            content=(
                                f"{name} ({symbol}) has unusual trading volume: "
                                f"${volume/1e6:.1f}M ({volume_ratio*100:.0f}% of market cap)"
                            ),
                            topics=[symbol, name, "Volume"],
                            metadata={
                                "name": name,
                                "symbol": symbol,
                                "volume": volume,
                                "market_cap": market_cap,
                                "volume_ratio": volume_ratio,
                            },
                            confidence=0.8,
                            urgency=7,
                        ))

        except Exception as e:
            logger.warning(f"CoinGecko top movers poll failed: {e}")

        return signals

    async def _poll_global_stats(self) -> list[Signal]:
        """Get global crypto market stats for context."""
        signals = []
        try:
            resp = await self.client.get(f"{self.BASE_URL}/global")
            resp.raise_for_status()
            data = resp.json().get("data", {})

            total_mcap = data.get("total_market_cap", {}).get("usd", 0)
            total_volume = data.get("total_volume", {}).get("usd", 0)
            btc_dominance = data.get("market_cap_percentage", {}).get("btc", 0)
            eth_dominance = data.get("market_cap_percentage", {}).get("eth", 0)
            active_cryptos = data.get("active_cryptocurrencies", 0)

            # Store as context signal (low urgency, always available)
            signals.append(Signal(
                source="coingecko",
                signal_type=SignalType.MARKET_CAP_SHIFT,
                title="Global crypto market snapshot",
                content=(
                    f"Total mcap: ${total_mcap/1e12:.2f}T. "
                    f"24h volume: ${total_volume/1e9:.1f}B. "
                    f"BTC dominance: {btc_dominance:.1f}%. "
                    f"ETH dominance: {eth_dominance:.1f}%. "
                    f"Active cryptos: {active_cryptos:,}"
                ),
                topics=["Market Overview"],
                metadata={
                    "total_mcap": total_mcap,
                    "total_volume": total_volume,
                    "btc_dominance": btc_dominance,
                    "eth_dominance": eth_dominance,
                    "active_cryptos": active_cryptos,
                },
                confidence=0.95,
                urgency=2,
            ))

        except Exception as e:
            logger.warning(f"CoinGecko global stats poll failed: {e}")

        return signals

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
