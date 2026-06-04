"""Research module for gathering data from free sources."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """A news item from RSS or API."""
    title: str
    summary: str
    source: str
    url: str
    published: str
    topics: list[str]


@dataclass
class ResearchResult:
    """Result of a research query."""
    topic: str
    findings: list[str]
    sources: list[str]
    sentiment: str
    confidence: float
    timestamp: str


class Researcher:
    """Research module for gathering crypto and tech intelligence."""

    def __init__(self, rss_feeds: list[str] | None = None):
        self.rss_feeds = rss_feeds or []
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_rss(self, url: str) -> list[NewsItem]:
        """Fetch and parse RSS feed."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            content = response.text

            items = []
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
                summary = re.sub(r"<[^>]+>", "", summary)[:200]

                link_m = link_pattern.search(item_xml)
                url_str = link_m.group(1) if link_m else ""

                pub_m = pub_pattern.search(item_xml)
                published = pub_m.group(1) if pub_m else ""

                if title:
                    items.append(NewsItem(
                        title=title.strip(),
                        summary=summary.strip(),
                        source=url,
                        url=url_str.strip(),
                        published=published.strip(),
                        topics=self._extract_topics(title + " " + summary),
                    ))

            return items[:10]
        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {url}: {e}")
            return []

    async def fetch_all_news(self) -> list[NewsItem]:
        """Fetch news from all configured RSS feeds."""
        all_items = []
        for feed_url in self.rss_feeds:
            items = await self.fetch_rss(feed_url)
            all_items.extend(items)

        all_items.sort(key=lambda x: x.published, reverse=True)
        return all_items[:20]

    def _extract_topics(self, text: str) -> list[str]:
        """Extract crypto-related topics from text."""
        text_lower = text.lower()
        topics = []

        crypto_keywords = {
            "bitcoin": "BTC", "btc": "BTC", "ethereum": "ETH", "eth": "ETH",
            "solana": "SOL", "sol": "SOL", "base": "BASE", "defi": "DeFi",
            "nft": "NFT", "dao": "DAO", "layer 2": "L2", "l2": "L2",
            "airdrop": "Airdrop", "memecoin": "Memecoin", "meme coin": "Memecoin",
            "ai": "AI", "artificial intelligence": "AI", "agentic": "Agentic",
            "stablecoin": "Stablecoin", "dex": "DEX", "cex": "CEX",
            "rug": "Security", "hack": "Security", "exploit": "Security",
            "governance": "Governance", "tokenomics": "Tokenomics",
        }

        for keyword, topic in crypto_keywords.items():
            if keyword in text_lower and topic not in topics:
                topics.append(topic)

        return topics

    async def research_topic(self, topic: str) -> ResearchResult:
        """Research a specific topic."""
        news = await self.fetch_all_news()

        relevant = []
        sources = []
        topic_lower = topic.lower()

        for item in news:
            if (topic_lower in item.title.lower() or
                topic_lower in item.summary.lower() or
                any(topic_lower in t.lower() for t in item.topics)):
                relevant.append(item.title)
                if item.url:
                    sources.append(item.url)

        if not relevant:
            for item in news[:5]:
                relevant.append(item.title)
                if item.url:
                    sources.append(item.url)

        sentiment = "neutral"
        negative_words = ["crash", "hack", "exploit", "rug", "fail", "drop", "bear"]
        positive_words = ["surge", "pump", "launch", "partnership", "growth", "bull"]

        all_text = " ".join(relevant).lower()
        neg_count = sum(1 for w in negative_words if w in all_text)
        pos_count = sum(1 for w in positive_words if w in all_text)

        if neg_count > pos_count:
            sentiment = "negative"
        elif pos_count > neg_count:
            sentiment = "positive"

        confidence = min(len(relevant) / 5.0, 1.0)

        return ResearchResult(
            topic=topic,
            findings=relevant[:5],
            sources=sources[:5],
            sentiment=sentiment,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
