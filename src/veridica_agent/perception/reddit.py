"""Reddit signal source — Crypto subreddit monitoring.

Monitors r/cryptocurrency, r/defi, and other crypto subreddits.
Free API: No key required, rate limited.
"""
from __future__ import annotations

import logging

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class RedditSource(SignalSource):
    """Fetches trending posts from crypto subreddits."""

    name = "reddit"
    BASE_URL = "https://www.reddit.com"
    RATE_LIMIT_PER_MINUTE = 10

    SUBREDDITS = [
        "cryptocurrency",
        "defi",
        "ethtrader",
        "bitcoin",
        "ethereum",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "VeridicaBot/1.0"},
        )

    async def poll(self) -> list[Signal]:
        """Poll Reddit for trending crypto posts."""
        signals: list[Signal] = []

        import asyncio
        tasks = [self._poll_subreddit(sub) for sub in self.SUBREDDITS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Reddit poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_subreddit(self, subreddit: str) -> list[Signal]:
        """Fetch hot posts from a subreddit."""
        signals = []
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/r/{subreddit}/hot.json",
                params={"limit": 10},
            )
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                score = post_data.get("score", 0)
                title = post_data.get("title", "")

                # High engagement posts
                if score > 1000:
                    signals.append(Signal(
                        source="reddit",
                        signal_type=SignalType.SENTIMENT_SHIFT,
                        title=f"r/{subreddit}: {title[:60]}",
                        content=f"High engagement post ({score} upvotes): {title}",
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        topics=["Reddit", subreddit],
                        metadata={
                            "subreddit": subreddit,
                            "score": score,
                            "comments": post_data.get("num_comments", 0),
                        },
                        confidence=0.6,
                        urgency=5 if score > 5000 else 3,
                    ))

        except Exception as e:
            logger.warning(f"Reddit r/{subreddit} failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
