"""Signal aggregator — combines all perception sources.

Rate limit policy:
- Sources WITH rate limits are PRIORITIZED (not skipped).
- A source is only skipped when its limit is actually exhausted.
- This reduces wasted API calls while maximizing data freshness.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from .base import Signal, SignalSource

logger = logging.getLogger(__name__)


class SignalAggregator:
    """Combines signals from all sources into a unified buffer."""

    def __init__(self):
        self.sources: list[SignalSource] = []
        self.signal_buffer: list[Signal] = []
        self.max_buffer_size = 200
        self.last_poll: datetime | None = None

    def add_source(self, source: SignalSource):
        """Register a signal source."""
        self.sources.append(source)
        logger.info(f"Registered signal source: {source.name}")

    def remove_source(self, name: str):
        """Unregister a signal source by name."""
        self.sources = [s for s in self.sources if s.name != name]

    async def poll_all(self) -> list[Signal]:
        """Poll all registered sources concurrently.

        Rate-limited sources are still polled — they self-check limits
        and return empty if exhausted. This keeps the flow simple.
        """
        enabled_sources = [s for s in self.sources if s.enabled]

        if not enabled_sources:
            logger.warning("No enabled signal sources")
            return []

        # Log rate limit status before polling
        for source in enabled_sources:
            status = source.get_rate_limit_status()
            if status.get("minute_limited") or status.get("day_limited"):
                logger.info(
                    f"  {source.name}: RATE LIMITED "
                    f"(minute: {status['minute_remaining']}/{status['minute_limit']}, "
                    f"day: {status['day_remaining']}/{status['day_limit']})"
                )

        logger.info(f"Polling {len(enabled_sources)} signal sources...")

        # Poll all sources concurrently
        tasks = [self._safe_poll(source) for source in enabled_sources]
        results = await asyncio.gather(*tasks)

        # Collect all signals
        all_signals: list[Signal] = []
        for source, signals in zip(enabled_sources, results):
            if signals:
                logger.info(f"  {source.name}: {len(signals)} signals")
                all_signals.extend(signals)

        # Deduplicate by title similarity
        deduplicated = self._deduplicate(all_signals)

        # Sort by urgency (highest first), then by timestamp (newest first)
        deduplicated.sort(key=lambda s: (s.urgency, s.timestamp), reverse=True)

        # Update buffer
        self.signal_buffer = deduplicated + self.signal_buffer
        if len(self.signal_buffer) > self.max_buffer_size:
            self.signal_buffer = self.signal_buffer[:self.max_buffer_size]

        self.last_poll = datetime.now()
        logger.info(f"Total signals after dedup: {len(deduplicated)}")

        return deduplicated

    async def _safe_poll(self, source: SignalSource) -> list[Signal]:
        """Poll a source with error handling and rate limit check."""
        # Check rate limit before polling (source also self-checks)
        if not source.rate_tracker.can_request():
            logger.debug(f"Source {source.name}: skipped (rate limited)")
            return []

        try:
            signals = await source.poll()
            # Record successful request
            source.rate_tracker.record()
            return signals
        except Exception as e:
            logger.warning(f"Source {source.name} failed: {e}")
            return []

    def _deduplicate(self, signals: list[Signal]) -> list[Signal]:
        """Remove duplicate signals based on title similarity."""
        seen_titles: set[str] = set()
        unique: list[Signal] = []

        for signal in signals:
            # Normalize title for comparison
            normalized = signal.title.lower().strip()
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(signal)

        return unique

    def get_buffer(self, limit: int = 50) -> list[Signal]:
        """Get recent signals from buffer."""
        return self.signal_buffer[:limit]

    def get_buffer_by_type(self, signal_type: str, limit: int = 20) -> list[Signal]:
        """Get signals filtered by type from buffer."""
        return [s for s in self.signal_buffer if s.signal_type.value == signal_type][:limit]

    def get_buffer_by_topic(self, topic: str, limit: int = 20) -> list[Signal]:
        """Get signals filtered by topic from buffer."""
        topic_lower = topic.lower()
        return [
            s for s in self.signal_buffer
            if any(topic_lower in t.lower() for t in s.topics)
        ][:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get aggregator statistics including rate limit status."""
        source_counts = {}
        for signal in self.signal_buffer:
            source_counts[signal.source] = source_counts.get(signal.source, 0) + 1

        type_counts = {}
        for signal in self.signal_buffer:
            type_counts[signal.signal_type.value] = type_counts.get(signal.signal_type.value, 0) + 1

        # Rate limit status per source
        rate_limits = {}
        for source in self.sources:
            rate_limits[source.name] = source.get_rate_limit_status()

        return {
            "sources_registered": len(self.sources),
            "sources_enabled": len([s for s in self.sources if s.enabled]),
            "buffer_size": len(self.signal_buffer),
            "last_poll": self.last_poll.isoformat() if self.last_poll else None,
            "signals_by_source": source_counts,
            "signals_by_type": type_counts,
            "rate_limits": rate_limits,
        }

    async def close(self):
        """Close all sources."""
        for source in self.sources:
            try:
                await source.close()
            except Exception as e:
                logger.warning(f"Error closing {source.name}: {e}")
