"""LunarCrush signal source — Social intelligence for crypto.

LunarCrush provides social sentiment, mention tracking, and influencer data.
API: https://lunarcrush.ai/
Free tier: 4 requests/min, 100/day (Hobby plan).
"""
from __future__ import annotations

import logging
import time

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class LunarCrushSource(SignalSource):
    """Fetches social sentiment from LunarCrush."""

    name = "lunarcrush"
    BASE_URL = "https://lunarcrush.ai/api4/public"

    # Rate limits (Hobby plan)
    RATE_LIMIT_PER_MINUTE = 4
    RATE_LIMIT_PER_DAY = 100

    def __init__(self, api_key: str = ""):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = api_key
        if api_key:
            self.client.headers["Authorization"] = f"Bearer {api_key}"

        # Rate limit tracking
        self._requests_this_minute: list[float] = []
        self._requests_today: list[float] = []
        self._minute_limit_hit = False
        self._daily_limit_hit = False

    def _check_rate_limit(self) -> bool:
        """Check if we can make a request. Returns True if OK, False if limited."""
        now = time.time()

        # Clean up minute window (sliding 60s)
        self._requests_this_minute = [
            t for t in self._requests_this_minute if now - t < 60
        ]

        # Clean up daily window (sliding 24h)
        self._requests_today = [
            t for t in self._requests_today if now - t < 86400
        ]

        # Check minute limit
        if len(self._requests_this_minute) >= self.RATE_LIMIT_PER_MINUTE:
            if not self._minute_limit_hit:
                logger.warning(
                    f"LunarCrush minute rate limit hit "
                    f"({self.RATE_LIMIT_PER_MINUTE}/min). "
                    f"Will resume when capacity available."
                )
                self._minute_limit_hit = True
            return False

        # Check daily limit
        if len(self._requests_today) >= self.RATE_LIMIT_PER_DAY:
            if not self._daily_limit_hit:
                logger.warning(
                    f"LunarCrush daily rate limit hit "
                    f"({self.RATE_LIMIT_PER_DAY}/day). "
                    f"Skipping until tomorrow."
                )
                self._daily_limit_hit = True
            return False

        self._minute_limit_hit = False
        return True

    def _record_request(self):
        """Record a successful API request for rate tracking."""
        now = time.time()
        self._requests_this_minute.append(now)
        self._requests_today.append(now)

    def get_rate_limit_status(self) -> dict:
        """Return current rate limit status for monitoring."""
        now = time.time()
        minute_used = len([
            t for t in self._requests_this_minute if now - t < 60
        ])
        day_used = len([
            t for t in self._requests_today if now - t < 86400
        ])
        return {
            "source": self.name,
            "minute_used": minute_used,
            "minute_limit": self.RATE_LIMIT_PER_MINUTE,
            "minute_remaining": max(0, self.RATE_LIMIT_PER_MINUTE - minute_used),
            "day_used": day_used,
            "day_limit": self.RATE_LIMIT_PER_DAY,
            "day_remaining": max(0, self.RATE_LIMIT_PER_DAY - day_used),
            "minute_limited": self._minute_limit_hit,
            "day_limited": self._daily_limit_hit,
        }

    async def poll(self) -> list[Signal]:
        """Poll LunarCrush for social intelligence signals."""
        signals: list[Signal] = []

        if not self._check_rate_limit():
            logger.debug("LunarCrush: rate limited, skipping poll")
            return signals

        import asyncio
        results = await asyncio.gather(
            self._poll_trending_topics(),
            self._poll_top_coins_social(),
            self._poll_sentiment_shifts(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"LunarCrush poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_trending_topics(self) -> list[Signal]:
        """Detect trending crypto topics on social media."""
        signals = []
        try:
            if not self._check_rate_limit():
                return signals

            resp = await self.client.get(f"{self.BASE_URL}/coins/list/v2")
            self._record_request()
            resp.raise_for_status()
            data = resp.json()
            coins = data.get("data", [])

            for coin in coins[:20]:
                name = coin.get("name", "")
                symbol = coin.get("symbol", "")
                social_score = coin.get("galaxy_score", 0)
                social_volume = coin.get("social_volume", 0)
                social_dominance = coin.get("social_dominance", 0)
                alt_rank = coin.get("alt_rank", 0)

                # High social activity with rising rank
                if social_dominance > 5 and alt_rank < 50:
                    signals.append(Signal(
                        source="lunarcrush",
                        signal_type=SignalType.NARRATIVE_EMERGENCE,
                        title=f"{name} ({symbol}) trending: social dominance {social_dominance:.1f}%",
                        content=f"{name} social dominance at {social_dominance:.1f}% "
                                f"with galaxy score {social_score}. "
                                f"Social volume: {social_volume:,}",
                        url=f"https://lunarcrush.com/coins/{symbol.lower()}",
                        topics=[name, symbol, "Social Trending"],
                        metadata={
                            "symbol": symbol,
                            "galaxy_score": social_score,
                            "social_volume": social_volume,
                            "social_dominance": social_dominance,
                            "alt_rank": alt_rank,
                        },
                        confidence=0.75,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"LunarCrush trending poll failed: {e}")

        return signals

    async def _poll_top_coins_social(self) -> list[Signal]:
        """Get social metrics for top coins."""
        signals = []
        try:
            if not self._check_rate_limit():
                return signals

            resp = await self.client.get(f"{self.BASE_URL}/coins/list/v2")
            self._record_request()
            resp.raise_for_status()
            data = resp.json()
            coins = data.get("data", [])

            for coin in coins[:10]:
                symbol = coin.get("symbol", "")
                sentiment = coin.get("sentiment", 0)
                social_volume_24h = coin.get("social_volume_24h", 0)
                social_volume_change = coin.get("social_volume_24h_change", 0)

                # Significant sentiment shift (>20% change)
                if abs(social_volume_change) > 20:
                    direction = "surged" if social_volume_change > 0 else "dropped"
                    signals.append(Signal(
                        source="lunarcrush",
                        signal_type=SignalType.SENTIMENT_SHIFT,
                        title=f"{symbol} social volume {direction} {abs(social_volume_change):.0f}%",
                        content=f"{symbol} social mentions {direction} "
                                f"{abs(social_volume_change):.0f}% in 24h. "
                                f"Current volume: {social_volume_24h:,}. "
                                f"Sentiment: {sentiment:.1f}/5",
                        url=f"https://lunarcrush.com/coins/{symbol.lower()}",
                        topics=[symbol, "Social Volume"],
                        metadata={
                            "symbol": symbol,
                            "sentiment": sentiment,
                            "social_volume_24h": social_volume_24h,
                            "volume_change": social_volume_change,
                        },
                        confidence=0.8,
                        urgency=7 if abs(social_volume_change) > 50 else 5,
                    ))

        except Exception as e:
            logger.warning(f"LunarCrush top coins poll failed: {e}")

        return signals

    async def _poll_sentiment_shifts(self) -> list[Signal]:
        """Detect major sentiment shifts across the market."""
        signals = []
        try:
            if not self._check_rate_limit():
                return signals

            resp = await self.client.get(f"{self.BASE_URL}/coins/list/v2")
            self._record_request()
            resp.raise_for_status()
            data = resp.json()
            coins = data.get("data", [])

            for coin in coins[:30]:
                symbol = coin.get("symbol", "")
                sentiment = coin.get("sentiment", 0)
                posts_active = coin.get("posts_active", 0)

                # Very negative sentiment with high activity = potential FUD
                if sentiment < 2 and posts_active > 100:
                    signals.append(Signal(
                        source="lunarcrush",
                        signal_type=SignalType.SENTIMENT_SHIFT,
                        title=f"{symbol} sentiment crash: {sentiment:.1f}/5 with {posts_active} active posts",
                        content=f"{symbol} experiencing severe negative sentiment "
                                f"({sentiment:.1f}/5) with {posts_active} active posts. "
                                f"Potential FUD or legitimate concern.",
                        url=f"https://lunarcrush.com/coins/{symbol.lower()}",
                        topics=[symbol, "FUD", "Negative Sentiment"],
                        metadata={
                            "symbol": symbol,
                            "sentiment": sentiment,
                            "posts_active": posts_active,
                        },
                        confidence=0.7,
                        urgency=8,
                    ))

        except Exception as e:
            logger.warning(f"LunarCrush sentiment poll failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
