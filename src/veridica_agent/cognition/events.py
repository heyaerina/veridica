"""Event detector — detects events that warrant Veridica's attention."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from ..perception.base import Signal, SignalType

logger = logging.getLogger(__name__)


class Event:
    """A detected event that may require Veridica to act."""

    def __init__(
        self,
        event_type: str,
        urgency: int,
        suggested_mode: str,
        title: str,
        description: str,
        topic: str = "",
        signals: list[Signal] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.event_type = event_type
        self.urgency = urgency
        self.suggested_mode = suggested_mode
        self.title = title
        self.description = description
        self.topic = topic
        self.signals = signals or []
        self.metadata = metadata or {}
        self.detected_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "urgency": self.urgency,
            "suggested_mode": self.suggested_mode,
            "title": self.title,
            "description": self.description,
            "topic": self.topic,
            "signal_count": len(self.signals),
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


class EventDetector:
    """Detects events from signals that warrant Veridica's attention."""

    def __init__(self):
        self.event_history: list[Event] = []
        self.cooldown_minutes = 30  # Don't re-detect same event within 30min
        self.last_detection: dict[str, datetime] = {}

    def evaluate(self, signals: list[Signal]) -> list[Event]:
        """Evaluate signals and detect events."""
        events: list[Event] = []

        # 1. Critical security events (highest priority)
        events.extend(self._detect_security_events(signals))

        # 2. Market anomalies
        events.extend(self._detect_market_anomalies(signals))

        # 3. Narrative convergence
        events.extend(self._detect_narrative_convergence(signals))

        # 4. Stablecoin depegs
        events.extend(self._detect_depegs(signals))

        # 5. Notable new protocols
        events.extend(self._detect_new_protocols(signals))

        # 6. Trending topics
        events.extend(self._detect_trending(signals))

        # Filter by cooldown
        events = self._filter_cooldown(events)

        # Sort by urgency
        events.sort(key=lambda e: e.urgency, reverse=True)

        # Record detection
        for event in events:
            self.event_history.append(event)
            self.last_detection[event.event_type] = datetime.now()

        if events:
            logger.info(f"Detected {len(events)} events, top: {events[0].title} (urgency={events[0].urgency})")

        return events

    def _detect_security_events(self, signals: list[Signal]) -> list[Event]:
        """Detect hacks, exploits, rugs."""
        events = []
        security_keywords = ["hack", "exploit", "drain", "rug", "scam", "stolen", "flash loan"]

        for signal in signals:
            text = (signal.title + " " + signal.content).lower()
            if any(kw in text for kw in security_keywords):
                events.append(Event(
                    event_type="SECURITY_INCIDENT",
                    urgency=9,
                    suggested_mode="AUTOPSY",
                    title=signal.title,
                    description=signal.content,
                    topic=signal.topics[0] if signal.topics else "Security",
                    signals=[signal],
                    metadata={"source": signal.source},
                ))

        return events

    def _detect_market_anomalies(self, signals: list[Signal]) -> list[Event]:
        """Detect significant price/volume movements."""
        events = []

        for signal in signals:
            # Price movements >20%
            if signal.signal_type == SignalType.PRICE_MOVEMENT:
                change = signal.metadata.get("change_24h", 0)
                if abs(change) > 20:
                    events.append(Event(
                        event_type="PRICE_ANOMALY",
                        urgency=8 if abs(change) > 30 else 6,
                        suggested_mode="WATCH",
                        title=signal.title,
                        description=signal.content,
                        topic=signal.metadata.get("symbol", "Unknown"),
                        signals=[signal],
                        metadata={"change_24h": change},
                    ))

            # TVL changes >25%
            if signal.signal_type == SignalType.TVL_CHANGE:
                change = signal.metadata.get("change_1d", 0)
                if abs(change) > 25:
                    events.append(Event(
                        event_type="TVL_ANOMALY",
                        urgency=7,
                        suggested_mode="SIGNAL",
                        title=signal.title,
                        description=signal.content,
                        topic=signal.metadata.get("protocol", "Unknown"),
                        signals=[signal],
                        metadata={"change_1d": change},
                    ))

            # Unusual volume
            if signal.signal_type == SignalType.VOLUME_SPIKE:
                ratio = signal.metadata.get("volume_ratio", 0)
                if ratio > 0.5:
                    events.append(Event(
                        event_type="VOLUME_ANOMALY",
                        urgency=7,
                        suggested_mode="SIGNAL",
                        title=signal.title,
                        description=signal.content,
                        topic=signal.metadata.get("symbol", signal.metadata.get("protocol", "Unknown")),
                        signals=[signal],
                    ))

        return events

    def _detect_narrative_convergence(self, signals: list[Signal]) -> list[Event]:
        """Detect when multiple sources converge on the same topic."""
        events = []
        topic_signals: dict[str, list[Signal]] = {}

        for signal in signals:
            for topic in signal.topics:
                if topic not in topic_signals:
                    topic_signals[topic] = []
                topic_signals[topic].append(signal)

        for topic, topic_sigs in topic_signals.items():
            # Need at least 3 different sources on the same topic
            unique_sources = set(s.source for s in topic_sigs)
            if len(unique_sources) >= 2 and len(topic_sigs) >= 3:
                events.append(Event(
                    event_type="NARRATIVE_CONVERGENCE",
                    urgency=6,
                    suggested_mode="SIGNAL",
                    title=f"Narrative converging: {topic}",
                    description=f"{len(topic_sigs)} signals from {len(unique_sources)} sources about {topic}",
                    topic=topic,
                    signals=topic_sigs,
                    metadata={
                        "signal_count": len(topic_sigs),
                        "source_count": len(unique_sources),
                    },
                ))

        return events

    def _detect_depegs(self, signals: list[Signal]) -> list[Event]:
        """Detect stablecoin depegs."""
        events = []

        for signal in signals:
            if signal.signal_type == SignalType.DEPEG:
                deviation = signal.metadata.get("deviation", 0)
                events.append(Event(
                    event_type="STABLECOIN_DEPEG",
                    urgency=9 if deviation > 0.05 else 7,
                    suggested_mode="WATCH",
                    title=signal.title,
                    description=signal.content,
                    topic=signal.metadata.get("stablecoin", "Unknown"),
                    signals=[signal],
                    metadata={"deviation": deviation},
                ))

        return events

    def _detect_new_protocols(self, signals: list[Signal]) -> list[Event]:
        """Detect notable new protocol launches."""
        events = []

        for signal in signals:
            if signal.signal_type == SignalType.NEW_PROTOCOL:
                tvl = signal.metadata.get("tvl", 0)
                if tvl > 5_000_000:  # >$5M TVL = notable
                    events.append(Event(
                        event_type="NEW_PROTOCOL",
                        urgency=6,
                        suggested_mode="SHIPCHECK",
                        title=signal.title,
                        description=signal.content,
                        topic=signal.metadata.get("protocol", "Unknown"),
                        signals=[signal],
                        metadata={"tvl": tvl},
                    ))

        return events

    def _detect_trending(self, signals: list[Signal]) -> list[Event]:
        """Detect trending topics worth investigating."""
        events = []

        trending = [s for s in signals if s.signal_type == SignalType.TRENDING]
        if trending:
            topics = []
            for s in trending:
                topics.extend(s.topics)

            topic_counts = Counter(topics)
            for topic, count in topic_counts.most_common(3):
                if count >= 2:
                    related_signals = [s for s in trending if topic in s.topics]
                    events.append(Event(
                        event_type="TRENDING_TOPIC",
                        urgency=5,
                        suggested_mode="WATCH",
                        title=f"Trending: {topic}",
                        description=f"{topic} is trending across multiple sources",
                        topic=topic,
                        signals=related_signals,
                    ))

        return events

    def _filter_cooldown(self, events: list[Event]) -> list[Event]:
        """Filter out events that are in cooldown period."""
        filtered = []
        now = datetime.now()

        for event in events:
            last = self.last_detection.get(event.event_type)
            if last:
                elapsed = (now - last).total_seconds() / 60
                if elapsed < self.cooldown_minutes:
                    logger.debug(f"Event {event.event_type} in cooldown ({elapsed:.0f}min)")
                    continue
            filtered.append(event)

        return filtered

    def get_recent_events(self, hours: int = 24) -> list[Event]:
        """Get events from the past N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.event_history if e.detected_at >= cutoff]

    def get_stats(self) -> dict:
        """Get event detection statistics."""
        event_type_counts = Counter(e.event_type for e in self.event_history)
        return {
            "total_events_detected": len(self.event_history),
            "events_by_type": dict(event_type_counts),
            "recent_24h": len(self.get_recent_events(24)),
        }
