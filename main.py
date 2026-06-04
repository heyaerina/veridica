"""Entry point for Veridica Agent — v2."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing config
load_dotenv(Path(__file__).resolve().parent / ".env")

from src.veridica_agent.agent import VeridicaAgent
from src.veridica_agent.config import load_config
from src.veridica_agent.modes import Mode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    root = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Veridica v2 — The Blind Observer of Crypto Twitter (Agentic Architecture)"
    )
    parser.add_argument("--config", type=str, default="config.local.json", help="Path to config JSON")

    # Run modes
    parser.add_argument("--once", action="store_true", help="Run one generation cycle and exit")
    parser.add_argument("--autonomous", action="store_true", help="Run in autonomous mode (event + schedule)")
    parser.add_argument("--topic", type=str, default="", help="Topic to analyze")
    parser.add_argument("--mode", type=str, choices=[m.value for m in Mode], help="Specific mode to use")
    parser.add_argument("--thread", type=int, help="Generate a thread with N tweets")

    # Status & management
    parser.add_argument("--status", action="store_true", help="Show agent status")
    parser.add_argument("--drafts", action="store_true", help="Show pending drafts")
    parser.add_argument("--reviews", action="store_true", help="Show pending reviews")
    parser.add_argument("--signals", action="store_true", help="Show recent signals from perception layer")
    parser.add_argument("--events", action="store_true", help="Show detected events")

    # Draft management
    parser.add_argument("--approve", type=str, help="Approve a draft by ID")
    parser.add_argument("--reject", type=str, help="Reject a draft by ID")
    parser.add_argument("--reject-reason", type=str, default="", help="Reason for rejection")

    args = parser.parse_args()

    config_path = (root / args.config).resolve()
    if not config_path.exists():
        fallback = root / "config.example.json"
        if args.config == "config.local.json" and fallback.exists():
            config_path = fallback
        else:
            raise SystemExit(f"Config not found: {config_path}")

    config = load_config(config_path)
    config.workspace_root = root
    agent = VeridicaAgent(config)

    try:
        # ── Status ──
        if args.status:
            status = agent.get_status()
            print(json.dumps(status, indent=2))
            return

        # ── Drafts ──
        if args.drafts:
            drafts = agent.draft_manager.get_pending_drafts()
            if drafts:
                print(f"\nPending drafts ({len(drafts)}):\n")
                for d in drafts:
                    print(f"  [{d.id}] {d.mode} on {d.topic} (confidence={d.confidence:.0%})")
                    print(f"    Trigger: {d.trigger}")
                    print(f"    Content: {d.content[:100]}...")
                    print()
            else:
                print("No pending drafts")
            return

        # ── Reviews ──
        if args.reviews:
            reviews = agent.review_queue.get_pending_reviews()
            if reviews:
                print(f"\nPending reviews ({len(reviews)}):\n")
                for r in reviews:
                    print(f"  - {r.name}")
            else:
                print("No pending reviews")
            return

        # ── Signals ──
        if args.signals:
            signals = agent.perception.get_buffer(20)
            if signals:
                print(f"\nRecent signals ({len(signals)}):\n")
                for s in signals:
                    print(f"  [{s.signal_type.value}] {s.title}")
                    print(f"    Source: {s.source} | Urgency: {s.urgency} | Topics: {', '.join(s.topics[:3])}")
                    print()
            else:
                print("No signals yet. Run --once or --autonomous first.")
            return

        # ── Events ──
        if args.events:
            events = agent.event_detector.get_recent_events(24)
            if events:
                print(f"\nRecent events ({len(events)}):\n")
                for e in events:
                    print(f"  [{e.event_type}] {e.title}")
                    print(f"    Urgency: {e.urgency} | Mode: {e.suggested_mode} | Topic: {e.topic}")
                    print()
            else:
                print("No events detected yet.")
            return

        # ── Approve draft ──
        if args.approve:
            draft = agent.draft_manager.approve_draft(args.approve)
            if draft:
                print(f"Draft approved: {draft.id}")
            else:
                print(f"Draft not found: {args.approve}")
            return

        # ── Reject draft ──
        if args.reject:
            draft = agent.draft_manager.reject_draft(args.reject, args.reject_reason)
            if draft:
                print(f"Draft rejected: {draft.id}")
            else:
                print(f"Draft not found: {args.reject}")
            return

        # ── Thread generation ──
        mode = Mode(args.mode) if args.mode else None

        if args.thread:
            topic = args.topic or "crypto market"
            tweets = await agent.generate_thread(topic, mode or Mode.SIGNAL, args.thread)
            print(f"\n{'='*60}")
            print(f"THREAD: {args.thread} tweets on '{topic}'")
            print(f"{'='*60}\n")
            for i, tweet in enumerate(tweets, 1):
                print(f"{i}. {tweet}\n")
            return

        # ── Autonomous mode ──
        if args.autonomous:
            await agent.run_autonomous()
            return

        # ── Single run ──
        if args.once or args.topic:
            result = await agent.run_once(topic=args.topic, mode=mode)
            if result:
                print(f"\n{'='*60}")
                print(f"Mode: {result['mode'].value}")
                print(f"Topic: {result['topic']}")
                print(f"Trigger: {result['trigger']}")
                print(f"Confidence: {result['confidence']:.0%}")
                print(f"Sentiment: {result.get('research_sentiment', 'N/A')}")
                print(f"{'='*60}")
                print(f"\n{result['content']}")
                print(f"\nDraft saved to: {config.safety.draft_directory}/")
            else:
                print("No content generated (check logs)")
            return

        # ── No args: show help ──
        parser.print_help()

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
