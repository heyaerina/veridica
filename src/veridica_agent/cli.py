"""Veridica CLI — The Blind Observer of Crypto Twitter."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv


def find_project_root() -> Path:
    """Find the project root (directory containing config files)."""
    # Check current working directory
    cwd = Path.cwd()
    if (cwd / "config.local.json").exists() or (cwd / "config.example.json").exists():
        return cwd

    # Check if we're inside the repo
    for parent in cwd.parents:
        if (parent / "config.local.json").exists() or (parent / "config.example.json").exists():
            return parent

    # Fallback to current directory
    return cwd


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )


async def run(args):
    """Main async entry point."""
    from .agent import VeridicaAgent
    from .config import load_config
    from .modes import Mode

    root = find_project_root()

    # Load .env
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Load config
    config_path = (root / args.config).resolve()
    if not config_path.exists():
        fallback = root / "config.example.json"
        if args.config == "config.local.json" and fallback.exists():
            config_path = fallback
        else:
            print(f"Error: Config not found: {config_path}")
            print(f"Run: cp config.example.json config.local.json")
            sys.exit(1)

    config = load_config(config_path)
    config.workspace_root = root
    agent = VeridicaAgent(config)

    try:
        # Status
        if args.status:
            status = agent.get_status()
            print(json.dumps(status, indent=2))
            return

        # Drafts
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

        # Reviews
        if args.reviews:
            reviews = agent.review_queue.get_pending_reviews()
            if reviews:
                print(f"\nPending reviews ({len(reviews)}):\n")
                for r in reviews:
                    print(f"  - {r.name}")
            else:
                print("No pending reviews")
            return

        # Signals
        if args.signals:
            signals = agent.perception.get_buffer(20)
            if signals:
                print(f"\nRecent signals ({len(signals)}):\n")
                for s in signals:
                    print(f"  [{s.signal_type.value}] {s.title}")
                    print(f"    Source: {s.source} | Urgency: {s.urgency} | Topics: {', '.join(s.topics[:3])}")
                    print()
            else:
                print("No signals yet. Run: veridica --once")
            return

        # Events
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

        # Approve draft
        if args.approve:
            draft = agent.draft_manager.approve_draft(args.approve)
            if draft:
                print(f"Draft approved: {draft.id}")
            else:
                print(f"Draft not found: {args.approve}")
            return

        # Reject draft
        if args.reject:
            draft = agent.draft_manager.reject_draft(args.reject, args.reject_reason)
            if draft:
                print(f"Draft rejected: {draft.id}")
            else:
                print(f"Draft not found: {args.reject}")
            return

        # Thread generation
        mode = Mode(args.mode) if args.mode else None

        if args.thread:
            topic = args.topic or "crypto market"
            tweets = await agent.generate_thread(topic, mode or Mode.PATTERN, args.thread)
            print(f"\n{'='*60}")
            print(f"THREAD: {args.thread} tweets on '{topic}'")
            print(f"{'='*60}\n")
            for i, tweet in enumerate(tweets, 1):
                print(f"{i}. {tweet}\n")
            return

        # Autonomous mode
        if args.autonomous:
            await agent.run_autonomous()
            return

        # Single run
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

        # No args: show help
        print_help()

    finally:
        await agent.close()


def print_help():
    """Print custom help message."""
    help_text = """
VERIDICA — The Blind Observer of Crypto Twitter

USAGE:
    veridica [OPTIONS]

RUN MODES:
    --once                  Run one generation cycle and exit
    --autonomous            Run in autonomous mode (event + schedule)
    --topic TOPIC           Topic to analyze
    --mode MODE             Specific mode (OBSERVE, PATTERN, INVESTIGATE, ROAST, BUILD, VERDICT)
    --thread N              Generate a thread with N tweets

STATUS:
    --status                Show agent status
    --drafts                Show pending drafts
    --reviews               Show pending reviews
    --signals               Show recent signals from perception layer
    --events                Show detected events

DRAFT MANAGEMENT:
    --approve ID            Approve a draft by ID
    --reject ID             Reject a draft by ID
    --reject-reason TEXT    Reason for rejection

CONFIG:
    --config PATH           Path to config JSON (default: config.local.json)

EXAMPLES:
    veridica --once                         Generate one draft
    veridica --once --topic "DeFi"          Generate draft about DeFi
    veridica --once --mode ROAST            Generate a roast
    veridica --autonomous                   Run continuously
    veridica --thread 5 --topic "Base"      Generate 5-tweet thread
    veridica --status                       Check agent status
    veridica --drafts                       View pending drafts
    veridica --approve OBSERVE_20260604_09  Approve a draft

MODES:
    OBSERVE      Watch, alert, chronicle, vibes
    PATTERN      Signal, predict, context, followup
    INVESTIGATE  Receipts, deep dive, compare, architect, pulse
    ROAST        Autopsy, deadweight, vaporcheck, redirect
    BUILD        Shipcheck, builder spotlight, migration
    VERDICT      Final judgment

For more: https://github.com/heyaerina/veridica
"""
    print(help_text)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="veridica",
        description="The Blind Observer of Crypto Twitter",
        add_help=False,
    )
    parser.add_argument("--config", type=str, default="config.local.json", help="Path to config JSON")

    # Run modes
    parser.add_argument("--once", action="store_true", help="Run one generation cycle")
    parser.add_argument("--autonomous", action="store_true", help="Run in autonomous mode")
    parser.add_argument("--topic", type=str, default="", help="Topic to analyze")
    parser.add_argument("--mode", type=str, help="Specific mode to use")
    parser.add_argument("--thread", type=int, help="Generate a thread with N tweets")

    # Status
    parser.add_argument("--status", action="store_true", help="Show agent status")
    parser.add_argument("--drafts", action="store_true", help="Show pending drafts")
    parser.add_argument("--reviews", action="store_true", help="Show pending reviews")
    parser.add_argument("--signals", action="store_true", help="Show recent signals")
    parser.add_argument("--events", action="store_true", help="Show detected events")

    # Draft management
    parser.add_argument("--approve", type=str, help="Approve a draft")
    parser.add_argument("--reject", type=str, help="Reject a draft")
    parser.add_argument("--reject-reason", type=str, default="", help="Rejection reason")

    # Help
    parser.add_argument("-h", "--help", action="store_true", help="Show help")

    args, _ = parser.parse_known_args()

    if args.help and not any([
        args.once, args.autonomous, args.status, args.drafts,
        args.reviews, args.signals, args.events, args.approve, args.reject
    ]):
        print_help()
        return

    setup_logging()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
