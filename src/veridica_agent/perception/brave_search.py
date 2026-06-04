"""Brave Search signal source — FREE web search API."""

from __future__ import annotations

import logging
import os

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class BraveSearchSource(SignalSource):
    """Searches the web for crypto intelligence using Brave Search API."""

    name = "brave_search"
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("BRAVE_SEARCH_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.queries_used = 0
        self.max_queries_per_run = 3  # Conserve free tier (2000/month)

    async def poll(self) -> list[Signal]:
        """Search for crypto-related content."""
        if not self.api_key:
            logger.info("Brave Search API key not set, skipping")
            return []

        signals: list[Signal] = []

        # Predefined search queries for CT intelligence
        queries = [
            "crypto breaking news today",
            "DeFi protocol launch announcement",
            "crypto hack exploit today",
            "new token launch trending",
        ]

        import asyncio
        tasks = [self._search(q) for q in queries[:self.max_queries_per_run]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Brave Search error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _search(self, query: str) -> list[Signal]:
        """Execute a single search query."""
        signals = []
        try:
            resp = await self.client.get(
                self.BASE_URL,
                params={"q": query, "count": 5, "freshness": "pd"},  # past day
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("web", {}).get("results", [])

            for item in results:
                title = item.get("title", "")
                description = item.get("description", "")
                url = item.get("url", "")
                age = item.get("age", "")

                if not title:
                    continue

                topics = self._extract_topics(title + " " + description)
                urgency = self._estimate_urgency(title, description)

                signals.append(Signal(
                    source="brave_search",
                    signal_type=SignalType.NEWS,
                    title=title,
                    content=description[:300],
                    url=url,
                    topics=topics,
                    metadata={
                        "query": query,
                        "age": age,
                    },
                    confidence=0.6,  # Web search results are less curated
                    urgency=urgency,
                ))

            self.queries_used += 1

        except Exception as e:
            logger.warning(f"Brave Search failed for '{query}': {e}")

        return signals

    def _extract_topics(self, text: str) -> list[str]:
        """Extract crypto topics from text."""
        text_lower = text.lower()
        topics = []
        keywords = {
            "bitcoin": "BTC", "btc": "BTC", "ethereum": "ETH", "eth": "ETH",
            "solana": "SOL", "defi": "DeFi", "nft": "NFT", "dao": "DAO",
            "layer 2": "L2", "airdrop": "Airdrop", "memecoin": "Memecoin",
            "ai": "AI", "stablecoin": "Stablecoin", "dex": "DEX",
            "hack": "Security", "exploit": "Security", "rug": "Security",
            "bridge": "Bridge", "staking": "Staking",
        }
        for keyword, topic in keywords.items():
            if keyword in text_lower and topic not in topics:
                topics.append(topic)
        return topics

    def _estimate_urgency(self, title: str, description: str) -> int:
        """Estimate urgency from search result."""
        text = (title + " " + description).lower()
        if any(w in text for w in ["hack", "exploit", "drain", "rug", "depeg"]):
            return 9
        if any(w in text for w in ["crash", "collapse", "sec ", "lawsuit"]):
            return 8
        if any(w in text for w in ["launch", "partnership", "record"]):
            return 7
        return 5

    def get_usage(self) -> dict:
        """Get API usage stats."""
        return {
            "queries_used": self.queries_used,
            "max_per_run": self.max_queries_per_run,
            "has_api_key": bool(self.api_key),
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
