"""Core agent for Veridica — v2 Agentic Architecture.

Perception → Cognition → Action → Output
Event-driven + Schedule-driven. Draft-first with human review.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Config
from .llm import LLMClient
from .memory import Memory
from .modes import Mode
from .research import Researcher
from .generator import ContentGenerator
from .safety import SafetyFilter, HumanReviewQueue
from .scheduler import Scheduler

# New perception layer
from .perception.base import Signal, SignalSource
from .perception.rss import RSSSource
from .perception.defillama import DeFiLlamaSource
from .perception.coingecko import CoinGeckoSource
from .perception.brave_search import BraveSearchSource
from .perception.github import GitHubSource
from .perception.aggregator import SignalAggregator

# New cognition layer
from .cognition.events import EventDetector, Event
from .cognition.mode_selector import ModeSelector, ModeDecision

# New output layer
from .output.draft_manager import DraftManager

logger = logging.getLogger(__name__)


class VeridicaAgent:
    """The main Veridica agent — v2 Agentic Architecture."""

    def __init__(self, config: Config):
        self.config = config
        self.root = config.workspace_root

        # ── Core (existing) ──
        self.llm = LLMClient(config.llm)
        self.memory = Memory(self.root / "data" / "memory.json")
        self.researcher = Researcher(config.research.rss_feeds)
        self.generator = ContentGenerator(config, self.llm, self.memory)
        self.safety = SafetyFilter(config.safety, self.memory)
        self.review_queue = HumanReviewQueue(self.root / "data" / "review_queue")
        self.scheduler = Scheduler(config.agent)

        # ── Perception (new) ──
        self.perception = SignalAggregator()
        self._setup_perception()

        # ── Cognition (new) ──
        self.event_detector = EventDetector()
        self.mode_selector = ModeSelector()

        # ── Output (new) ──
        self.draft_manager = DraftManager(
            draft_dir=self.root / config.safety.draft_directory,
            review_dir=self.root / config.safety.review_directory,
        )

        # ── State ──
        self.running = False
        self.cycle_count = 0

    def _setup_perception(self):
        """Register all enabled signal sources."""
        pc = self.config.perception

        if pc.enable_rss:
            self.perception.add_source(RSSSource(pc.rss_feeds))

        if pc.enable_defillama:
            self.perception.add_source(DeFiLlamaSource())

        if pc.enable_coingecko:
            self.perception.add_source(CoinGeckoSource())

        if pc.enable_brave_search and pc.brave_search_api_key:
            self.perception.add_source(BraveSearchSource(pc.brave_search_api_key))

        if pc.enable_github:
            self.perception.add_source(GitHubSource())

    # ═══════════════════════════════════════════════════════════
    #  MAIN AUTONOMOUS LOOP — Event-driven + Schedule-driven
    # ═══════════════════════════════════════════════════════════

    async def run_autonomous(self):
        """Flexible autonomous loop: event-driven + schedule-driven."""
        self.running = True
        logger.info("=" * 60)
        logger.info("Veridica v2 — Agentic Autonomous Mode")
        logger.info("=" * 60)
        logger.info(self.scheduler.calendar.get_schedule_summary())
        logger.info(f"Perception sources: {len(self.perception.sources)}")
        for source in self.perception.sources:
            logger.info(f"  - {source.name} (enabled={source.enabled})")
        logger.info("=" * 60)

        while self.running:
            try:
                self.cycle_count += 1
                logger.info(f"--- Cycle {self.cycle_count} ---")

                # ── Phase 1: PERCEIVE ──
                signals = await self.perception.poll_all()
                logger.info(f"Perceived {len(signals)} signals")

                # ── Phase 2: DETECT EVENTS ──
                events = self.event_detector.evaluate(signals)

                # ── Phase 3: DECIDE ──
                decision = self._decide(signals, events)
                logger.info(f"Decision: {decision.mode.value} (confidence={decision.confidence:.2f}, trigger={decision.trigger})")
                logger.info(f"  Reason: {decision.reason}")

                # ── Phase 4: ACT ──
                if decision.trigger == "idle":
                    await self._idle_tasks(signals)
                    await asyncio.sleep(self.config.agent.idle_poll_interval)
                    continue

                result = await self._execute(decision, signals)

                # ── Phase 5: OUTPUT ──
                if result:
                    await self._output(result, decision)

                # ── Sleep ──
                interval = (
                    self.config.agent.active_poll_interval
                    if decision.trigger == "event"
                    else self.config.agent.idle_poll_interval
                )
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in cycle {self.cycle_count}: {e}", exc_info=True)
                await asyncio.sleep(10)

        logger.info("Autonomous mode stopped")

    def _decide(self, signals: list[Signal], events: list[Event]) -> ModeDecision:
        """Decide what to do based on signals and events."""
        threshold = self.config.agent.event_urgency_threshold

        # Priority 1: High-urgency events
        if events and events[0].urgency >= threshold:
            return self.mode_selector.select_from_event(events[0])

        # Priority 2: Scheduled time
        if self.scheduler.should_run():
            calendar_mode = self.scheduler.calendar.get_mode_for_now()
            return self.mode_selector.select_from_schedule(calendar_mode.value)

        # Priority 3: Signal-based decision
        if signals:
            recent_modes = self.memory.get_recent_modes(5)
            decision = self.mode_selector.select_from_signals(signals, recent_modes)
            if decision.confidence >= 0.7:
                return decision

        # Default: idle
        return ModeDecision(
            mode=Mode.WATCH,
            confidence=0.3,
            reason="No significant signals or events",
            trigger="idle",
        )

    async def _execute(self, decision: ModeDecision, signals: list[Signal]) -> dict | None:
        """Execute a decision — generate content."""
        mode = decision.mode
        topic = decision.topic or "crypto market"

        # Research the topic
        research = await self.researcher.research_topic(topic)

        # Generate content based on mode
        if mode == Mode.AUTOPSY:
            content = await self.generator.generate_roast(
                project=topic,
                issue=decision.reason,
                context="; ".join(research.findings[:3]),
            )
        elif mode in [Mode.SIGNAL, Mode.RECEIPTS, Mode.VERDICT]:
            content = await self.generator.generate_analysis(
                topic=topic,
                research=research,
                mode=mode,
            )
        else:
            content = await self.generator.generate_tweet(
                mode=mode,
                topic=topic,
                research=research,
            )

        if not content:
            logger.warning("No content generated")
            return None

        return {
            "content": content,
            "mode": mode,
            "topic": topic,
            "trigger": decision.trigger,
            "confidence": decision.confidence,
            "research_sentiment": research.sentiment,
            "research_findings": research.findings[:3],
        }

    async def _output(self, result: dict, decision: ModeDecision):
        """Handle output: safety check → draft → review queue."""
        content = result["content"]
        mode = result["mode"]
        topic = result["topic"]

        # Safety validation
        validation = self.safety.validate_tweet(content, mode.value)

        if not validation["approved"]:
            logger.warning(f"Content rejected by safety: {validation['errors']}")
            return

        # Create draft (always)
        draft = self.draft_manager.create_draft(
            content=content,
            mode=mode.value,
            topic=topic,
            trigger=decision.trigger,
            event_type=decision.metadata.get("event_type", "") if decision.metadata else "",
            confidence=decision.confidence,
            metadata={
                "research_sentiment": result.get("research_sentiment"),
                "research_findings": result.get("research_findings", []),
            },
        )

        # Queue for review if needed
        if validation["requires_review"]:
            reason = "; ".join(validation["warnings"])
            self.review_queue.add_to_queue(content, mode.value, topic, reason)
            logger.info(f"Queued for review: {reason}")

        # Update memory
        self.memory.add_tweet(content, mode, topic)
        self.memory.add_mode(mode)

        # Mark scheduler run
        self.scheduler.mark_run()

        logger.info(f"Draft saved: {draft.id} ({draft.status})")

    async def _idle_tasks(self, signals: list[Signal]):
        """Lightweight tasks during idle time."""
        # Log signals to memory for pattern detection
        for signal in signals[:10]:
            self.memory.log_signal(signal)

    # ═══════════════════════════════════════════════════════════
    #  SINGLE RUN (existing, enhanced)
    # ═══════════════════════════════════════════════════════════

    async def run_once(self, topic: str = "", mode: Mode | None = None):
        """Run a single content generation cycle."""
        logger.info("Starting single generation cycle")

        # Perceive
        signals = await self.perception.poll_all()

        # Detect events
        events = self.event_detector.evaluate(signals)

        # Decide
        if not mode:
            if events and events[0].urgency >= self.config.agent.event_urgency_threshold:
                decision = self.mode_selector.select_from_event(events[0])
            else:
                decision = self.mode_selector.select_from_signals(signals)
            mode = decision.mode
        else:
            decision = ModeDecision(
                mode=mode,
                confidence=1.0,
                reason="Manually specified",
                trigger="manual",
            )

        if not topic:
            topic = decision.topic or self._select_topic(signals)

        # Execute
        decision.topic = topic
        result = await self._execute(decision, signals)

        # Output
        if result:
            await self._output(result, decision)

        return result

    def _select_topic(self, signals: list[Signal]) -> str:
        """Select topic from signals."""
        if not signals:
            return "crypto market observation"

        # Find highest urgency signal with topics
        for signal in signals:
            if signal.topics:
                return signal.topics[0]

        return signals[0].title if signals else "crypto market"

    # ═══════════════════════════════════════════════════════════
    #  THREAD GENERATION (existing)
    # ═══════════════════════════════════════════════════════════

    async def generate_thread(
        self,
        topic: str,
        mode: Mode = Mode.SIGNAL,
        tweet_count: int = 5,
    ) -> list[str]:
        """Generate a tweet thread."""
        research = await self.researcher.research_topic(topic)
        tweets = await self.generator.generate_thread(
            mode=mode,
            topic=topic,
            research=research,
            tweet_count=tweet_count,
        )

        for i, tweet in enumerate(tweets, 1):
            self.memory.add_tweet(tweet, mode, f"{topic} (thread {i}/{len(tweets)})")

        return tweets

    # ═══════════════════════════════════════════════════════════
    #  STATUS & MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def get_status(self) -> dict:
        """Get comprehensive agent status."""
        return {
            "agent": self.config.agent.name,
            "version": "2.0",
            "running": self.running,
            "cycle_count": self.cycle_count,
            "scheduler": self.scheduler.get_status(),
            "memory": self.memory.get_stats(),
            "perception": self.perception.get_stats(),
            "events": self.event_detector.get_stats(),
            "drafts": self.draft_manager.get_stats(),
            "pending_reviews": len(self.review_queue.get_pending_reviews()),
        }

    def stop(self):
        """Stop the autonomous loop."""
        self.running = False
        logger.info("Stop requested")

    async def close(self):
        """Close all connections."""
        await self.llm.close()
        await self.researcher.close()
        await self.perception.close()
