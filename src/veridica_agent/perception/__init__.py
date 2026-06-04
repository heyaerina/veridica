"""Perception layer — Multi-source intelligence gathering."""

from .base import Signal, SignalSource, SignalType, Event
from .aggregator import SignalAggregator
from .github import GitHubSource

__all__ = [
    "Signal",
    "SignalSource",
    "SignalType",
    "Event",
    "SignalAggregator",
    "GitHubSource",
]
