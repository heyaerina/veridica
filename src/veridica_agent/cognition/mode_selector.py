"""Enhanced mode selector — context-aware mode selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..modes import Mode, MODE_DESCRIPTIONS
from ..perception.base import Signal

logger = logging.getLogger(__name__)


@dataclass
class ModeDecision:
    """A mode selection decision with reasoning."""

    mode: Mode
    confidence: float   # 0.0 - 1.0
    reason: str
    topic: str = ""
    trigger: str = ""   # "event", "schedule", "idle"
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "topic": self.topic,
            "trigger": self.trigger,
        }


class ModeSelector:
    """Intelligent mode selection based on signals, events, and context."""

    # Maps event types to modes
    EVENT_MODE_MAP = {
        "SECURITY_INCIDENT": Mode.AUTOPSY,
        "PRICE_ANOMALY": Mode.WATCH,
        "TVL_ANOMALY": Mode.SIGNAL,
        "VOLUME_ANOMALY": Mode.SIGNAL,
        "NARRATIVE_CONVERGENCE": Mode.SIGNAL,
        "STABLECOIN_DEPEG": Mode.WATCH,
        "NEW_PROTOCOL": Mode.SHIPCHECK,
        "TRENDING_TOPIC": Mode.WATCH,
    }

    def select_from_signals(
        self,
        signals: list[Signal],
        recent_modes: list[Mode] | None = None,
    ) -> ModeDecision:
        """Select mode based on signal analysis."""
        if not signals:
            return ModeDecision(
                mode=Mode.WATCH,
                confidence=0.5,
                reason="No signals available",
                trigger="idle",
            )

        candidates: list[tuple[Mode, float, str]] = []

        # Analyze signal types
        type_counts: dict[str, int] = {}
        for signal in signals:
            st = signal.signal_type.value
            type_counts[st] = type_counts.get(st, 0) + 1

        # Security signals → AUTOPSY
        if type_counts.get("news", 0) > 0:
            security_signals = [
                s for s in signals
                if any(w in (s.title + s.content).lower()
                       for w in ["hack", "exploit", "rug", "drain"])
            ]
            if security_signals:
                candidates.append((
                    Mode.AUTOPSY,
                    0.9,
                    f"Security incident detected: {security_signals[0].title[:50]}"
                ))

        # Volume/price spikes → SIGNAL
        spike_count = type_counts.get("volume_spike", 0) + type_counts.get("price_movement", 0)
        if spike_count >= 2:
            candidates.append((
                Mode.SIGNAL,
                0.8,
                f"Multiple market anomalies detected ({spike_count} signals)"
            ))

        # TVL changes → RECEIPTS
        if type_counts.get("tvl_change", 0) >= 2:
            candidates.append((
                Mode.RECEIPTS,
                0.7,
                f"TVL data available for analysis ({type_counts['tvl_change']} protocols)"
            ))

        # New protocols → SHIPCHECK
        if type_counts.get("new_protocol", 0) > 0:
            candidates.append((
                Mode.SHIPCHECK,
                0.7,
                "New protocol(s) detected for investigation"
            ))

        # Depegs → WATCH
        if type_counts.get("depeg", 0) > 0:
            candidates.append((
                Mode.WATCH,
                0.85,
                "Stablecoin depeg detected"
            ))

        # Narrative convergence → SIGNAL
        if type_counts.get("narrative_emergence", 0) > 0:
            candidates.append((
                Mode.SIGNAL,
                0.75,
                "Emerging narrative detected"
            ))

        # Default: WATCH
        if not candidates:
            candidates.append((
                Mode.WATCH,
                0.5,
                "Monitoring market conditions"
            ))

        # Variety bonus: avoid repeating recent modes
        if recent_modes:
            last_mode = recent_modes[-1]
            candidates = [
                (mode, score + (0.1 if mode != last_mode else 0), reason)
                for mode, score, reason in candidates
            ]

        # Select best candidate
        best = max(candidates, key=lambda c: c[1])
        mode, confidence, reason = best

        # Extract primary topic from signals
        topic = self._extract_primary_topic(signals)

        return ModeDecision(
            mode=mode,
            confidence=confidence,
            reason=reason,
            topic=topic,
            trigger="signal_analysis",
        )

    def select_from_event(self, event: Any) -> ModeDecision:
        """Select mode based on a detected event."""
        event_type = event.event_type if hasattr(event, 'event_type') else str(event.get("event_type", ""))

        mode = self.EVENT_MODE_MAP.get(event_type, Mode.WATCH)

        title = event.title if hasattr(event, 'title') else event.get("title", "")
        topic = event.topic if hasattr(event, 'topic') else event.get("topic", "")

        return ModeDecision(
            mode=mode,
            confidence=0.9,
            reason=f"Event detected: {title}",
            topic=topic,
            trigger="event",
            metadata=event.to_dict() if hasattr(event, 'to_dict') else event,
        )

    def select_from_schedule(self, calendar_mode: str = "WATCH") -> ModeDecision:
        """Select mode based on schedule/calendar."""
        try:
            mode = Mode(calendar_mode)
        except ValueError:
            mode = Mode.WATCH

        return ModeDecision(
            mode=mode,
            confidence=0.6,
            reason=f"Scheduled mode: {calendar_mode}",
            trigger="schedule",
        )

    def _extract_primary_topic(self, signals: list[Signal]) -> str:
        """Extract the most relevant topic from signals."""
        topic_counts: dict[str, int] = {}
        for signal in signals:
            for topic in signal.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        if topic_counts:
            return max(topic_counts, key=topic_counts.get)
        return "crypto market"
