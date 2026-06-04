"""Mode system for Veridica Agent."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Mode(str, Enum):
    """Veridica's operational modes."""
    WATCH = "WATCH"
    SIGNAL = "SIGNAL"
    RECEIPTS = "RECEIPTS"
    REDIRECT = "REDIRECT"
    AUTOPSY = "AUTOPSY"
    DEADWEIGHT = "DEADWEIGHT"
    SHIPCHECK = "SHIPCHECK"
    VERDICT = "VERDICT"


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
    Mode.WATCH: {
        "trigger": "Something deserves attention",
        "action": "Observe and note without conclusion",
        "output": "Short observation tweet",
    },
    Mode.SIGNAL: {
        "trigger": "A pattern is emerging",
        "action": "Point out what consensus hasn't noticed",
        "output": "Thread or single tweet highlighting the pattern",
    },
    Mode.RECEIPTS: {
        "trigger": "Evidence is available",
        "action": "Present facts and data",
        "output": "Evidence-backed analysis",
    },
    Mode.REDIRECT: {
        "trigger": "Timeline is distracted",
        "action": "Redirect attention to what matters",
        "output": "Provocative redirect tweet",
    },
    Mode.AUTOPSY: {
        "trigger": "Something failed",
        "action": "Explain the failure points",
        "output": "Post-mortem analysis with lessons",
    },
    Mode.DEADWEIGHT: {
        "trigger": "Something is slowing progress",
        "action": "Identify the drag",
        "output": "Critical observation with suggestion",
    },
    Mode.SHIPCHECK: {
        "trigger": "Claims need verification",
        "action": "Investigate building vs performing",
        "output": "Reality check on project claims",
    },
    Mode.VERDICT: {
        "trigger": "Enough evidence accumulated",
        "action": "Render judgment",
        "output": "Definitive take",
    },
}


def select_mode(context: str, recent_modes: list[Mode] | None = None) -> Mode:
    """Select appropriate mode based on context."""
    context_lower = context.lower()

    if any(word in context_lower for word in ["failed", "crash", "exploit", "hack", "rug"]):
        return Mode.AUTOPSY

    if any(word in context_lower for word in ["slow", "stuck", "delayed", "vaporware"]):
        return Mode.DEADWEIGHT

    if any(word in context_lower for word in ["building", "shipping", "launching", "delivering"]):
        return Mode.SHIPCHECK

    if any(word in context_lower for word in ["evidence", "data", "proof", "onchain"]):
        return Mode.RECEIPTS

    if any(word in context_lower for word in ["pattern", "trend", "emerging", "noticed"]):
        return Mode.SIGNAL

    if any(word in context_lower for word in ["distracted", "noise", "wrong", "focus"]):
        return Mode.REDIRECT

    if any(word in context_lower for word in ["verdict", "conclusion", "final", "enough"]):
        return Mode.VERDICT

    if recent_modes:
        last_mode = recent_modes[-1]
        if last_mode == Mode.WATCH:
            return Mode.SIGNAL

    return Mode.WATCH
