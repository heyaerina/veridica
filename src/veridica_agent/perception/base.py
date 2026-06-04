"""Base classes for the perception layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    """Types of signals Veridica can perceive."""

    # News & content
    NEWS = "news"
    ANALYSIS = "analysis"
    RUMOR = "rumor"

    # On-chain
    TVL_CHANGE = "tvl_change"
    VOLUME_SPIKE = "volume_spike"
    WHALE_MOVEMENT = "whale_movement"
    NEW_PROTOCOL = "new_protocol"
    DEPEG = "depeg"
    BRIDGE_FLOW = "bridge_flow"

    # Market
    PRICE_MOVEMENT = "price_movement"
    TRENDING = "trending"
    MARKET_CAP_SHIFT = "market_cap_shift"

    # Social
    MENTION = "mention"
    SENTIMENT_SHIFT = "sentiment_shift"
    NARRATIVE_EMERGENCE = "narrative_emergence"

    # Developer
    GITHUB_ACTIVITY = "github_activity"
    CONTRACT_DEPLOY = "contract_deploy"
    TRENDING_REPO = "trending_repo"

    # Meta
    UNKNOWN = "unknown"


@dataclass
class Signal:
    """A single intelligence signal from any source."""

    source: str              # "rss", "defillama", "coingecko", "brave", etc.
    signal_type: SignalType
    title: str               # Short description
    content: str             # Full content / summary
    url: str = ""            # Source URL
    topics: list[str] = field(default_factory=list)   # Extracted topics
    metadata: dict[str, Any] = field(default_factory=dict)  # Source-specific data
    confidence: float = 0.5  # 0.0 - 1.0
    urgency: int = 5         # 1-10, 10 = act now
    timestamp: datetime = field(default_factory=lambda: datetime.now().replace(tzinfo=None))

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "signal_type": self.signal_type.value,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "topics": self.topics,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "urgency": self.urgency,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Event:
    """A detected event that may require Veridica's attention."""

    event_type: str          # "TVL_ANOMALY", "VOLUME_SPIKE", "NARRATIVE", etc.
    urgency: int             # 1-10
    suggested_mode: str      # Mode name suggestion
    title: str               # Short title
    description: str         # What happened
    signals: list[Signal] = field(default_factory=list)  # Signals that triggered this
    topic: str = ""          # Primary topic
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "urgency": self.urgency,
            "suggested_mode": self.suggested_mode,
            "title": self.title,
            "description": self.description,
            "topic": self.topic,
            "signal_count": len(self.signals),
            "metadata": self.metadata,
        }


class SignalSource(ABC):
    """Base class for all signal sources."""

    name: str = "base"
    enabled: bool = True

    @abstractmethod
    async def poll(self) -> list[Signal]:
        """Fetch signals from this source."""
        ...

    @abstractmethod
    async def close(self):
        """Clean up resources."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} enabled={self.enabled}>"
