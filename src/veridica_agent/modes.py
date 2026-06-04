"""Mode system for Veridica Agent — 6 consolidated modes."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Mode(str, Enum):
    """Veridica's 6 consolidated operational modes."""

    OBSERVE = "OBSERVE"       # Watch, alert, chronicle, vibes
    PATTERN = "PATTERN"       # Signal, predict, context, followup
    INVESTIGATE = "INVESTIGATE"  # Receipts, deep dive, compare, architect, pulse
    ROAST = "ROAST"           # Autopsy, deadweight, vaporcheck, redirect
    BUILD = "BUILD"           # Shipcheck, builder spotlight, migration
    VERDICT = "VERDICT"       # Final judgment


@dataclass
class ModeContext:
    """Context for a specific mode activation."""
    mode: Mode
    trigger: str
    topic: str
    evidence: list[str]
    timestamp: datetime
    priority: int = 5


MODE_DESCRIPTIONS = {
    Mode.OBSERVE: {
        "trigger": "Something deserves attention — breaking news, vibe shift, or chronicle update",
        "action": "Observe and note. Share what caught your attention without drawing conclusions yet.",
        "output": "Short observation, alert, or vibe check",
        "sub_modes": "WATCH, ALERT, CHRONICLE, VIBES",
    },
    Mode.PATTERN: {
        "trigger": "A pattern is emerging, a prediction can be made, or context is needed",
        "action": "Point out what consensus hasn't noticed. Connect the dots. Show the sequence.",
        "output": "Pattern highlight, prediction, narrative tracking, or followup",
        "sub_modes": "SIGNAL, PREDICT, CONTEXT, FOLLOWUP",
    },
    Mode.INVESTIGATE: {
        "trigger": "Evidence is available, a topic needs deep analysis, or comparison is warranted",
        "action": "Present facts, dig deeper, compare, analyze structure, or assess community health.",
        "output": "Evidence-backed analysis, deep dive, comparison, or community pulse",
        "sub_modes": "RECEIPTS, DEEP_DIVE, COMPARE, ARCHITECT, PULSE",
    },
    Mode.ROAST: {
        "trigger": "Something failed, is dragging progress, is overhyped, or the timeline is distracted",
        "action": "Explain the failure, identify the drag, call out the hype, or redirect attention.",
        "output": "Post-mortem, critique, vapor check, or redirect",
        "sub_modes": "AUTOPSY, DEADWEIGHT, VAPORCHECK, REDIRECT",
    },
    Mode.BUILD: {
        "trigger": "Claims need verification, a builder deserves spotlight, or ecosystem is shifting",
        "action": "Reality check on claims, highlight real development, or track ecosystem movement.",
        "output": "Ship check, builder spotlight, or migration analysis",
        "sub_modes": "SHIPCHECK, BUILDER_SPOTLIGHT, MIGRATION",
    },
    Mode.VERDICT: {
        "trigger": "Enough evidence has accumulated to render judgment",
        "action": "Deliver a definitive take. Final word on the matter.",
        "output": "Definitive judgment with supporting reasoning",
        "sub_modes": "VERDICT",
    },
}


def select_mode(context: str, recent_modes: list[Mode] | None = None) -> Mode:
    """Select appropriate mode based on context keywords."""
    context_lower = context.lower()

    # ROAST triggers
    if any(word in context_lower for word in ["failed", "crash", "exploit", "hack", "rug", "scam"]):
        return Mode.ROAST
    if any(word in context_lower for word in ["slow", "stuck", "delayed", "vaporware", "overhyped"]):
        return Mode.ROAST
    if any(word in context_lower for word in ["distracted", "noise", "wrong focus", "redirect"]):
        return Mode.ROAST

    # BUILD triggers
    if any(word in context_lower for word in ["building", "shipping", "launching", "delivering", "commits"]):
        return Mode.BUILD
    if any(word in context_lower for word in ["developer", "dev activity", "github", "migration"]):
        return Mode.BUILD

    # INVESTIGATE triggers
    if any(word in context_lower for word in ["evidence", "data", "proof", "onchain", "compare"]):
        return Mode.INVESTIGATE
    if any(word in context_lower for word in ["deep dive", "analysis", "tokenomics", "community"]):
        return Mode.INVESTIGATE

    # PATTERN triggers
    if any(word in context_lower for word in ["pattern", "trend", "emerging", "noticed", "predict"]):
        return Mode.PATTERN
    if any(word in context_lower for word in ["followup", "update", "context", "history"]):
        return Mode.PATTERN

    # VERDICT triggers
    if any(word in context_lower for word in ["verdict", "conclusion", "final", "enough", "judgment"]):
        return Mode.VERDICT

    # Default: OBSERVE, with variety
    if recent_modes:
        last_mode = recent_modes[-1]
        if last_mode == Mode.OBSERVE:
            return Mode.PATTERN

    return Mode.OBSERVE
