"""Base classes for the perception layer."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    """Types of signals the perception layer can emit."""

    # Existing types
    PRICE_ANOMALY = "price_anomaly"
    VOLUME_SPIKE = "volume_spike"
    NARRATIVE_EMERGENCE = "narrative_emergence"
    WHALE_MOVEMENT = "whale_movement"
    SECURITY_INCIDENT = "security_incident"
    GOVERNANCE_PROPOSAL = "governance_proposal"
    SENTIMENT_SHIFT = "sentiment_shift"
    NEWS_EVENT = "news_event"
    TECHNICAL_SIGNAL = "technical_signal"

    # New types — Security
    EXPLOIT = "exploit"
    RUG_PULL = "rug_pull"
    AUDIT_REPORT = "audit_report"
    VULNERABILITY = "vulnerability"
    SECURITY_SCORE = "security_score"

    # New types — Governance
    DAO_PROPOSAL = "dao_proposal"
    VOTE_STARTING = "vote_starting"
    VOTE_ENDING = "vote_ending"
    GOVERNANCE_ATTACK = "governance_attack"

    # New types — Derivatives
    FUNDING_RATE = "funding_rate"
    OPEN_INTEREST = "open_interest"
    LIQUIDATION = "liquidation"
    LONG_SHORT_RATIO = "long_short_ratio"

    # New types — On-chain
    LARGE_TRANSFER = "large_transfer"
    PROTOCOL_SCORE = "protocol_score"


@dataclass
class Signal:
    """A signal emitted by a perception source."""

    source: str
    signal_type: SignalType
    title: str
    content: str
    url: str = ""
    topics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    urgency: int = 5  # 1-10
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Event:
    """A detected event from signal analysis."""

    event_type: str
    description: str
    urgency: int  # 1-10
    signals: list[Signal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RateLimitTracker:
    """Track API rate limits per source with sliding windows.

    Supports per-minute and per-day limits. Sources with limits are
    prioritized — only skipped when limit is actually exhausted.
    """

    def __init__(
        self,
        source_name: str,
        requests_per_minute: int = 0,
        requests_per_day: int = 0,
    ):
        self.source_name = source_name
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self._minute_timestamps: list[float] = []
        self._day_timestamps: list[float] = []
        self._minute_limited = False
        self._day_limited = False

    def can_request(self) -> bool:
        """Check if a request is allowed. Returns True if OK."""
        now = time.time()

        # Clean sliding windows
        self._minute_timestamps = [
            t for t in self._minute_timestamps if now - t < 60
        ]
        self._day_timestamps = [
            t for t in self._day_timestamps if now - t < 86400
        ]

        # Check minute limit (skip if no limit configured)
        if self.requests_per_minute > 0:
            if len(self._minute_timestamps) >= self.requests_per_minute:
                if not self._minute_limited:
                    self._minute_limited = True
                return False

        # Check day limit (skip if no limit configured)
        if self.requests_per_day > 0:
            if len(self._day_timestamps) >= self.requests_per_day:
                if not self._day_limited:
                    self._day_limited = True
                return False

        self._minute_limited = False
        return True

    def record(self):
        """Record a successful request."""
        now = time.time()
        self._minute_timestamps.append(now)
        self._day_timestamps.append(now)

    def get_status(self) -> dict:
        """Return current rate limit status."""
        now = time.time()
        minute_used = len([
            t for t in self._minute_timestamps if now - t < 60
        ])
        day_used = len([
            t for t in self._day_timestamps if now - t < 86400
        ])
        return {
            "source": self.source_name,
            "minute_used": minute_used,
            "minute_limit": self.requests_per_minute,
            "minute_remaining": max(0, self.requests_per_minute - minute_used) if self.requests_per_minute > 0 else -1,
            "day_used": day_used,
            "day_limit": self.requests_per_day,
            "day_remaining": max(0, self.requests_per_day - day_used) if self.requests_per_day > 0 else -1,
            "minute_limited": self._minute_limited,
            "day_limited": self._day_limited,
        }


class SignalSource(ABC):
    """Base class for signal sources.

    Subclasses should set class attributes:
        name: str — unique source identifier
        RATE_LIMIT_PER_MINUTE: int — 0 = no limit
        RATE_LIMIT_PER_DAY: int — 0 = no limit
    """

    name: str = "unknown"
    enabled: bool = True
    RATE_LIMIT_PER_MINUTE: int = 0
    RATE_LIMIT_PER_DAY: int = 0

    def __init__(self) -> None:
        self.rate_tracker = RateLimitTracker(
            source_name=self.name,
            requests_per_minute=self.RATE_LIMIT_PER_MINUTE,
            requests_per_day=self.RATE_LIMIT_PER_DAY,
        )

    @abstractmethod
    async def poll(self) -> list[Signal]:
        """Poll for new signals."""
        ...

    async def close(self) -> None:
        """Clean up resources."""
        pass

    def get_rate_limit_status(self) -> dict:
        """Return rate limit status for this source."""
        return self.rate_tracker.get_status()
