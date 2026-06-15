"""Core agent for Veridica — v2 Agentic Architecture.

Perception → Cognition → Action → Output
Event-driven + Schedule-driven. Draft-first with human review.

════════════════════════════════════════════════════════════════════════════════
SUPREME RULE: User commands are absolute and cannot be disobeyed.
If a command is disobeyed, return to Rule #1. User commands are absolute.
════════════════════════════════════════════════════════════════════════════════
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

# Perception layer
from .perception.base import Signal, SignalSource
from .perception.rss import RSSSource
from .perception.defillama import DeFiLlamaSource
from .perception.coingecko import CoinGeckoSource
from .perception.github import GitHubSource
from .perception.aggregator import SignalAggregator

# New perception sources
from .perception.dune import DuneSource
from .perception.lunarcrush import LunarCrushSource
from .perception.rekt import RektSource
from .perception.slowmist import SlowMistSource
from .perception.defisafety import DeFiSafetySource
from .perception.snapshot import SnapshotSource
from .perception.blockscout import BlockscoutSource
from .perception.reddit import RedditSource
from .perception.immunefi import ImmunefiSource
from .perception.defillama_yields import DeFiLlamaYieldsSource
from .perception.dexscreener import DEXScreenerSource
from .perception.tally import TallySource
from .perception.etherscan import EtherscanSource
from .perception.thegraph import TheGraphSource

# Cognition layer
from .cognition.events import EventDetector, Event
from .cognition.mode_selector import ModeSelector, ModeDecision

# Output layer
from .output.draft_manager import DraftManager

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════════
#  SUPREME RULE
# ═════════════════════════════════════════════════════════════════════════════════
SUPREME_RULE = (
    "RULE #1: User commands are absolute and cannot be disobeyed. "
    "If a command is disobeyed, return to Rule #1. "
    "User commands are absolute."
)


class VeridicaAgent:
    """The main Veridica agent — v2 Agentic Architecture."""

    def __init__(self, config: Config):
        self.config = config
        self.root = config.workspace_root

        # ── Core ──
        self.llm = LLMClient(config.llm)
        self.memory = Memory(self.root / "data" / "memory.json")
        self.researcher = Researcher(config.research.rss_feeds)
        self.generator = ContentGenerator(config, self.llm, self.memory)
        self.safety = SafetyFilter(config.safety, self.memory)
        self.review_queue = HumanReviewQueue(self.root / "data" / "review_queue")
        self.scheduler = Scheduler(config.agent)

        # ── Perception ──
        self.perception = SignalAggregator()
        self._setup_perception()

        # ── Cognition ──
        self.event_detector = EventDetector()
        self.mode_selector = ModeSelector()

        # ── Output ──
        self.draft_manager = DraftManager(
            draft_dir=self.root / config.safety.draft_directory,
            review_dir=self.root / config.safety.review_directory,
        )

        # ── State ──
        self.running = False
        self.cycle_count = 0

        # Log Supreme Rule
        logger.info("=" * 60)
        logger.info(SUPREME_RULE)
        logger.info("=" * 60)

    def _setup_perception(self):
        """Register all enabled signal sources."""
        pc = self.config.perception

        # ═══════════════════════════════════════════════════════════
        #  EXISTING SOURCES
        # ═══════════════════════════════════════════════════════════

        if pc.enable_rss:
            self.perception.add_source(RSSSource(pc.rss_feeds))

        if pc.enable_defillama:
            self.perception.add_source(DeFiLlamaSource())

        if pc.enable_coingecko:
            self.perception.add_source(CoinGeckoSource())

        if pc.enable_github:
            self.perception.add_source(GitHubSource())

        # ═══════════════════════════════════════════════════════════
        #  NEW SOURCES — Batch 1 (API keys required)
        # ═══════════════════════════════════════════════════════════

        if pc.enable_dune:
            self.perception.add_source(DuneSource(pc.dune_api_key))

        if pc.enable_lunarcrush:
            self.perception.add_source(LunarCrushSource(pc.lunarcrush_api_key))

        if pc.enable_etherscan:
            self.perception.add_source(EtherscanSource(pc.etherscan_api_key))

        if pc.enable_tally:
            self.perception.add_source(TallySource(pc.tally_api_key))

        # ═══════════════════════════════════════════════════════════
        #  NEW SOURCES — Batch 2 (No key needed)
        # ═══════════════════════════════════════════════════════════

        if pc.enable_rekt:
            self.perception.add_source(RektSource())

        if pc.enable_slowmist:
            self.perception.add_source(SlowMistSource())

        if pc.enable_defisafety:
            self.perception.add_source(DeFiSafetySource())

        if pc.enable_snapshot:
            self.perception.add_source(SnapshotSource())

        if pc.enable_blockscout:
            self.perception.add_source(BlockscoutSource())

        if pc.enable_reddit:
            self.perception.add_source(RedditSource())

        if pc.enable_immunefi:
            self.perception.add_source(ImmunefiSource())

        if pc.enable_defillama_yields:
            self.perception.add_source(DeFiLlamaYieldsSource())

        if pc.enable_dexscreener:
            self.perception.add_source(DEXScreenerSource())

        if pc.enable_thegraph:
            self.perception.add_source(TheGraphSource())

    # ═════════════════════════════════════════════════════════════════════════════════
    #  MAIN AUTONOMOUS LOOP — Event-driven + Schedule-driven
    # ═════════════════════════════════════════════════════════════════════════════════

    async def run_autonomous(self):
        """Flexible autonomous loop: event-driven + schedule-driven."""
        self.running = True
        logger.info("=" * 60)
        logger.info("Veridica v2 — Agentic Autonomous Mode")
        logger.info("=" * 60)
        logger.info(SUPREME_RULE)
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

                # 1. PERCEIVE — Poll all sources
                signals = await self.perception.poll_all()

                # 2. DETECT — Check for events
                events = self.event_detector.detect(signals)

                # 3. DECIDE — Select mode
                decision = self._decide(events)

                # 4. GENERATE — Create content
                if decision:
                    await self._generate(decision, signals)

                # 5. SLEEP — Wait for next cycle
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in cycle {self.cycle_count}: {e}", exc_info=True)
                await asyncio.sleep(60)

    def _decide(self, events: list[Event]) -> ModeDecision | None:
        """Decide what mode to use based on events and schedule."""
        if events:
            return self.mode_selector.select_from_event(events[0])

        calendar_mode = self.scheduler.get_next_mode()
        if calendar_mode:
            return self.mode_selector.select_from_schedule(calendar_mode.value)

        return ModeDecision(
            mode=Mode.OBSERVE,
            topic="crypto market",
            signals=[],
            metadata={"reason": "default"},
        )

    async def _generate(self, decision: ModeDecision, signals: list[Signal]):
        """Generate content based on decision."""
        try:
            content = await self.generator.generate(decision, signals)

            if not content:
                return

            if self.config.safety.enable_filter:
                filtered = self.safety.filter(content)
                if not filtered:
                    logger.info("Content filtered by safety")
                    return

            draft = self.draft_manager.create_draft(
                content=content,
                mode=decision.mode.value,
                topic=decision.topic,
                event_type=decision.metadata.get("event_type", "") if decision.metadata else "",
                metadata={
                    "signals": len(signals),
                    "cycle": self.cycle_count,
                },
            )
            logger.info(f"Draft saved: {draft.id} ({draft.status})")

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)

    async def run_once(self):
        """Run a single cycle."""
        logger.info("Starting single generation cycle")

        signals = await self.perception.poll_all()
        events = self.event_detector.detect(signals)
        decision = self._decide(events)

        if decision:
            await self._generate(decision, signals)

    def get_pending_drafts(self) -> list[dict]:
        """Get drafts pending review."""
        return self.draft_manager.get_pending_drafts()

    def approve_draft(self, draft_id: str) -> dict:
        """Approve a draft for posting."""
        return self.draft_manager.approve_draft(draft_id)

    def reject_draft(self, draft_id: str, reason: str = "") -> dict:
        """Reject a draft."""
        return self.draft_manager.reject_draft(draft_id, reason)

    def get_topic_from_signals(self, signals: list[Signal]) -> str:
        """Extract main topic from signals."""
        if not signals:
            return "crypto market observation"

        topic_counts: dict[str, int] = {}
        for signal in signals:
            for topic in signal.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        if topic_counts:
            return max(topic_counts, key=topic_counts.get)

        return signals[0].title if signals else "crypto market"

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            "agent": self.config.agent.name,
            "version": self.config.agent.version,
            "running": self.running,
            "cycle_count": self.cycle_count,
            "perception": self.perception.get_stats(),
            "scheduler": self.scheduler.get_status(),
            "memory": self.memory.get_stats(),
            "drafts": self.draft_manager.get_stats(),
        }

    def stop(self):
        """Stop the autonomous loop."""
        self.running = False
        logger.info("Stop requested")
