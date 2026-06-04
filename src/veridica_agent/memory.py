"""Memory system for Veridica Agent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .modes import Mode

logger = logging.getLogger(__name__)


@dataclass
class TweetRecord:
    """Record of a generated or posted tweet."""
    id: str
    content: str
    mode: str
    topic: str
    created_at: str
    posted: bool = False
    posted_at: str | None = None
    engagement_score: float | None = None


@dataclass
class ProjectRecord:
    """Record of a tracked project."""
    name: str
    ticker: str
    first_seen: str
    last_analyzed: str
    sentiment: str = "neutral"
    notes: list[str] = field(default_factory=list)
    roast_count: int = 0


@dataclass
class SignalRecord:
    """Record of a perceived signal."""
    source: str
    signal_type: str
    title: str
    topics: list[str]
    urgency: int
    timestamp: str


@dataclass
class MemoryState:
    """Persistent memory state."""
    tweets: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    recent_modes: list[str] = field(default_factory=list)
    topics_covered: list[str] = field(default_factory=list)
    signals: list[dict] = field(default_factory=list)
    last_updated: str = ""


class Memory:
    """Memory system for tracking posts, projects, and patterns."""

    def __init__(self, memory_path: Path):
        self.memory_path = memory_path
        self.state = self._load()

    def _load(self) -> MemoryState:
        """Load memory from file."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return MemoryState(**data)
            except Exception as e:
                logger.warning(f"Failed to load memory: {e}")
        return MemoryState()

    def _save(self):
        """Save memory to file."""
        self.state.last_updated = datetime.now().isoformat()
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.state), f, indent=2)

    def add_tweet(self, content: str, mode: Mode, topic: str) -> TweetRecord:
        """Add a new tweet to memory."""
        tweet = TweetRecord(
            id=f"tweet_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            content=content,
            mode=mode.value,
            topic=topic,
            created_at=datetime.now().isoformat(),
        )
        self.state.tweets.append(asdict(tweet))
        self.state.topics_covered.append(topic)
        self._save()
        return tweet

    def mark_posted(self, tweet_id: str):
        """Mark a tweet as posted."""
        for tweet in self.state.tweets:
            if tweet["id"] == tweet_id:
                tweet["posted"] = True
                tweet["posted_at"] = datetime.now().isoformat()
                break
        self._save()

    def get_recent_tweets(self, count: int = 10) -> list[dict]:
        """Get recent tweets."""
        return self.state.tweets[-count:]

    def get_draft_tweets(self) -> list[dict]:
        """Get unposted tweets."""
        return [t for t in self.state.tweets if not t.get("posted")]

    def add_mode(self, mode: Mode):
        """Record a mode usage."""
        self.state.recent_modes.append(mode.value)
        if len(self.state.recent_modes) > 20:
            self.state.recent_modes = self.state.recent_modes[-20:]
        self._save()

    def get_recent_modes(self, count: int = 5) -> list[Mode]:
        """Get recent modes used."""
        recent = self.state.recent_modes[-count:]
        return [Mode(m) for m in recent if m in Mode.__members__]

    def update_project(self, name: str, ticker: str, sentiment: str, note: str):
        """Update or add project information."""
        existing = None
        for p in self.state.projects:
            if p["name"].lower() == name.lower() or p["ticker"].lower() == ticker.lower():
                existing = p
                break

        if existing:
            existing["last_analyzed"] = datetime.now().isoformat()
            existing["sentiment"] = sentiment
            existing["notes"].append(note)
            if sentiment == "negative":
                existing["roast_count"] += 1
        else:
            project = ProjectRecord(
                name=name,
                ticker=ticker,
                first_seen=datetime.now().isoformat(),
                last_analyzed=datetime.now().isoformat(),
                sentiment=sentiment,
                notes=[note],
                roast_count=1 if sentiment == "negative" else 0,
            )
            self.state.projects.append(asdict(project))

        self._save()

    def get_project(self, name: str) -> dict | None:
        """Get project information."""
        for p in self.state.projects:
            if p["name"].lower() == name.lower():
                return p
        return None

    def get_all_projects(self) -> list[dict]:
        """Get all tracked projects."""
        return self.state.projects

    def was_topic_covered(self, topic: str, days: int = 7) -> bool:
        """Check if a topic was recently covered."""
        topic_lower = topic.lower()
        recent_topics = self.state.topics_covered[-50:]
        return any(topic_lower in t.lower() for t in recent_topics)

    def log_signal(self, signal: Any):
        """Log a perceived signal to memory."""
        record = {
            "source": signal.source if hasattr(signal, "source") else "unknown",
            "signal_type": signal.signal_type.value if hasattr(signal.signal_type, "value") else str(signal.signal_type),
            "title": signal.title if hasattr(signal, "title") else "",
            "topics": signal.topics if hasattr(signal, "topics") else [],
            "urgency": signal.urgency if hasattr(signal, "urgency") else 5,
            "timestamp": datetime.now().isoformat(),
        }
        self.state.signals.append(record)

        # Keep only last 500 signals
        if len(self.state.signals) > 500:
            self.state.signals = self.state.signals[-500:]

        self._save()

    def get_recent_signals(self, count: int = 20) -> list[dict]:
        """Get recent signals."""
        return self.state.signals[-count:]

    def get_stats(self) -> dict:
        """Get memory statistics."""
        total_tweets = len(self.state.tweets)
        posted_tweets = len([t for t in self.state.tweets if t.get("posted")])
        projects_tracked = len(self.state.projects)
        signals_logged = len(self.state.signals)

        return {
            "total_tweets": total_tweets,
            "posted_tweets": posted_tweets,
            "draft_tweets": total_tweets - posted_tweets,
            "projects_tracked": projects_tracked,
            "signals_logged": signals_logged,
            "last_updated": self.state.last_updated,
        }
