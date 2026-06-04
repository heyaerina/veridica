"""RSS feed signal source — refactored from research.py."""

from __future__ import annotations

import logging
import re
from datetime import datetime

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)

# Crypto topic extraction keywords
CRYPTO_KEYWORDS = {
    "bitcoin": "BTC", "btc": "BTC", "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL", "base": "BASE", "defi": "DeFi",
    "nft": "NFT", "dao": "DAO", "layer 2": "L2", "l2": "L2",
    "airdrop": "Airdrop", "memecoin": "Memecoin", "meme coin": "Memecoin",
    "ai": "AI", "artificial intelligence": "AI", "agentic": "Agentic",
    "stablecoin": "Stablecoin", "dex": "DEX", "cex": "CEX",
    "rug": "Security", "hack": "Security", "exploit": "Security",
    "governance": "Governance", "tokenomics": "Tokenomics",
    "bridge": "Bridge", "staking": "Staking", "yield": "Yield",
    "launch": "Launch", "airdrop": "Airdrop", "token": "Token",
}

NEGATIVE_WORDS = ["crash", "hack", "exploit", "rug", "fail", "drop", "bear", "scam", "drain"]
POSITIVE_WORDS = ["surge", "pump", "launch", "partnership", "growth", "bull", "milestone", "record"]


class RSSSource(SignalSource):
    """Fetches intelligence from RSS feeds."""

    name = "rss"

    def __init__(self, feed_urls: list[str] | None = None):
        self.feed_urls = feed_urls or [
            "https://cointelegraph.com/rss",
            "https://coindesk.com/arc/outboundfeeds/rss/",
            "https://decrypt.co/feed",
            "https://www.theblock.co/rss.xml",
        ]
        self.client = httpx.AsyncClient(timeout=30.0)

    async def poll(self) -> list[Signal]:
        """Fetch and parse all RSS feeds into signals."""
        all_signals: list[Signal] = []

        for url in self.feed_urls:
            try:
                items = await self._fetch_feed(url)
                all_signals.extend(items)
            except Exception as e:
                logger.warning(f"RSS fetch failed for {url}: {e}")

        # Sort by published date, newest first
        all_signals.sort(key=lambda s: s.timestamp, reverse=True)
        return all_signals[:20]

    async def _fetch_feed(self, url: str) -> list[Signal]:
        """Fetch and parse a single RSS feed."""
        response = await self.client.get(url)
        response.raise_for_status()
        content = response.text

        signals = []
        item_pattern = re.compile(r"<item>(.*?)</item>", re.DOTALL)
        title_pattern = re.compile(r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>")
        desc_pattern = re.compile(r"<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>")
        link_pattern = re.compile(r"<link>(.*?)</link>")
        pub_pattern = re.compile(r"<pubDate>(.*?)</pubDate>")

        for item_match in item_pattern.finditer(content[:50000]):
            item_xml = item_match.group(1)

            title_m = title_pattern.search(item_xml)
            title = (title_m.group(1) or title_m.group(2)) if title_m else ""

            desc_m = desc_pattern.search(item_xml)
            summary = (desc_m.group(1) or desc_m.group(2)) if desc_m else ""
            summary = re.sub(r"<[^>]+>", "", summary)[:300]

            link_m = link_pattern.search(item_xml)
            url_str = link_m.group(1) if link_m else ""

            pub_m = pub_pattern.search(item_xml)
            published = pub_m.group(1) if pub_m else ""

            if not title:
                continue

            topics = self._extract_topics(title + " " + summary)
            sentiment = self._analyze_sentiment(title + " " + summary)
            urgency = self._estimate_urgency(title, summary, topics)

            signals.append(Signal(
                source="rss",
                signal_type=SignalType.NEWS,
                title=title.strip(),
                content=summary.strip(),
                url=url_str.strip(),
                topics=topics,
                metadata={
                    "published": published.strip(),
                    "sentiment": sentiment,
                    "feed_url": url,
                },
                confidence=0.7,
                urgency=urgency,
                timestamp=self._parse_date(published),
            ))

        return signals[:10]

    def _extract_topics(self, text: str) -> list[str]:
        """Extract crypto-related topics from text."""
        text_lower = text.lower()
        topics = []
        for keyword, topic in CRYPTO_KEYWORDS.items():
            if keyword in text_lower and topic not in topics:
                topics.append(topic)
        return topics

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        text_lower = text.lower()
        neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        if neg > pos:
            return "negative"
        elif pos > neg:
            return "positive"
        return "neutral"

    def _estimate_urgency(self, title: str, summary: str, topics: list[str]) -> int:
        """Estimate urgency 1-10 based on content."""
        text = (title + " " + summary).lower()
        urgency = 5  # baseline

        # High urgency signals
        if any(w in text for w in ["hack", "exploit", "drain", "rug", "depeg"]):
            urgency = 9
        elif any(w in text for w in ["crash", "collapse", "bankrupt", "sec ", "lawsuit"]):
            urgency = 8
        elif any(w in text for w in ["launch", "partnership", "record", "milestone"]):
            urgency = 7
        elif any(w in text for w in ["trend", "surge", "pump", "growth"]):
            urgency = 6

        return min(urgency, 10)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse RSS date string."""
        if not date_str:
            return datetime.now()
        try:
            # RFC 2822 format: "Wed, 04 Jun 2026 12:00:00 +0000"
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            # Strip timezone to avoid comparison issues
            return dt.replace(tzinfo=None)
        except Exception:
            return datetime.now()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
