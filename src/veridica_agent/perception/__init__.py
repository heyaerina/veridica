"""Perception layer — Multi-source intelligence gathering."""

from .base import Signal, SignalSource, SignalType, Event
from .aggregator import SignalAggregator
from .github import GitHubSource

# New sources
from .dune import DuneSource
from .lunarcrush import LunarCrushSource
from .rekt import RektSource
from .slowmist import SlowMistSource
from .defisafety import DeFiSafetySource
from .snapshot import SnapshotSource
from .blockscout import BlockscoutSource
from .reddit import RedditSource
from .immunefi import ImmunefiSource
from .defillama_yields import DeFiLlamaYieldsSource
from .dexscreener import DEXScreenerSource
from .tally import TallySource
from .etherscan import EtherscanSource
from .thegraph import TheGraphSource

__all__ = [
    "Signal", "SignalSource", "SignalType", "Event",
    "SignalAggregator", "GitHubSource",
    "DuneSource", "LunarCrushSource", "RektSource", "SlowMistSource",
    "DeFiSafetySource", "SnapshotSource",
    "BlockscoutSource", "RedditSource", "ImmunefiSource",
    "DeFiLlamaYieldsSource", "DEXScreenerSource", "TallySource",
    "EtherscanSource", "TheGraphSource",
]
