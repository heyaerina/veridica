"""Configuration loader for Veridica Agent."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LLMConfig:
    """LLM API configuration."""
    api_key: str = ""
    base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    model: str = "mimo-v2.5-pro"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class AgentConfig:
    """Agent behavior configuration."""
    name: str = "Veridica"
    autonomous_mode: bool = True
    cycle_interval_minutes: int = 60
    max_tweets_per_day: int = 8
    max_research_per_day: int = 4
    content_calendar: dict = field(default_factory=lambda: {
        "morning": {"hour": 9, "mode": "WATCH"},
        "midday": {"hour": 13, "mode": "SIGNAL"},
        "evening": {"hour": 18, "mode": "VERDICT"},
    })
    # New: event-driven settings
    event_urgency_threshold: int = 7      # Minimum urgency to trigger immediate action
    idle_poll_interval: int = 30           # Seconds between polls during idle
    active_poll_interval: int = 10         # Seconds between polls during active events


@dataclass
class SafetyConfig:
    """Safety and rate limiting configuration."""
    require_human_review: bool = True
    draft_directory: str = "data/tweets"
    review_directory: str = "data/review_queue"
    blocked_topics: list = field(default_factory=lambda: [
        "financial advice", "price predictions", "guaranteed returns"
    ])
    rate_limit_window_minutes: int = 60
    max_posts_per_window: int = 2


@dataclass
class ResearchConfig:
    """Research data source configuration."""
    rss_feeds: list = field(default_factory=lambda: [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
    ])
    cryptopanic_api_key: str = ""
    enable_onchain: bool = False


@dataclass
class PerceptionConfig:
    """Perception layer configuration."""
    # RSS
    enable_rss: bool = True
    rss_feeds: list = field(default_factory=lambda: [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
        "https://www.theblock.co/rss.xml",
    ])

    # DeFiLlama (free, no key)
    enable_defillama: bool = True

    # CoinGecko (free, no key)
    enable_coingecko: bool = True

    # Brave Search (free with key)
    enable_brave_search: bool = False
    brave_search_api_key: str = ""

    # GitHub (free, no key for public repos)
    enable_github: bool = True

    # General
    signal_buffer_size: int = 200
    poll_timeout: int = 30


@dataclass
class Config:
    """Main configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    perception: PerceptionConfig = field(default_factory=PerceptionConfig)
    workspace_root: Path = field(default_factory=lambda: Path.cwd())


def load_config(config_path: Path | str) -> Config:
    """Load configuration from JSON file with environment variable overrides."""
    config_path = Path(config_path)

    config = Config()

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "llm" in data:
            for key, value in data["llm"].items():
                if hasattr(config.llm, key):
                    setattr(config.llm, key, value)

        if "agent" in data:
            for key, value in data["agent"].items():
                if hasattr(config.agent, key):
                    setattr(config.agent, key, value)

        if "safety" in data:
            for key, value in data["safety"].items():
                if hasattr(config.safety, key):
                    setattr(config.safety, key, value)

        if "research" in data:
            for key, value in data["research"].items():
                if hasattr(config.research, key):
                    setattr(config.research, key, value)

        if "perception" in data:
            for key, value in data["perception"].items():
                if hasattr(config.perception, key):
                    setattr(config.perception, key, value)

    # Environment variable overrides
    if os.getenv("VERIDICA_API_KEY"):
        config.llm.api_key = os.getenv("VERIDICA_API_KEY", "")

    if os.getenv("VERIDICA_BASE_URL"):
        config.llm.base_url = os.getenv("VERIDICA_BASE_URL", "")

    if os.getenv("VERIDICA_MODEL"):
        config.llm.model = os.getenv("VERIDICA_MODEL", "")

    if os.getenv("BRAVE_SEARCH_API_KEY"):
        config.perception.brave_search_api_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
        config.perception.enable_brave_search = True

    return config


def save_config(config: Config, config_path: Path | str) -> None:
    """Save configuration to JSON file."""
    config_path = Path(config_path)

    data = {
        "llm": {
            "base_url": config.llm.base_url,
            "model": config.llm.model,
            "max_tokens": config.llm.max_tokens,
            "temperature": config.llm.temperature,
        },
        "agent": {
            "name": config.agent.name,
            "autonomous_mode": config.agent.autonomous_mode,
            "cycle_interval_minutes": config.agent.cycle_interval_minutes,
            "max_tweets_per_day": config.agent.max_tweets_per_day,
            "max_research_per_day": config.agent.max_research_per_day,
            "content_calendar": config.agent.content_calendar,
            "event_urgency_threshold": config.agent.event_urgency_threshold,
            "idle_poll_interval": config.agent.idle_poll_interval,
            "active_poll_interval": config.agent.active_poll_interval,
        },
        "safety": {
            "require_human_review": config.safety.require_human_review,
            "draft_directory": config.safety.draft_directory,
            "review_directory": config.safety.review_directory,
            "blocked_topics": config.safety.blocked_topics,
            "rate_limit_window_minutes": config.safety.rate_limit_window_minutes,
            "max_posts_per_window": config.safety.max_posts_per_window,
        },
        "perception": {
            "enable_rss": config.perception.enable_rss,
            "rss_feeds": config.perception.rss_feeds,
            "enable_defillama": config.perception.enable_defillama,
            "enable_coingecko": config.perception.enable_coingecko,
            "enable_brave_search": config.perception.enable_brave_search,
            "signal_buffer_size": config.perception.signal_buffer_size,
        },
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
