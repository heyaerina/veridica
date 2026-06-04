"""Safety features for Veridica Agent."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import SafetyConfig
from .memory import Memory

logger = logging.getLogger(__name__)


class SafetyFilter:
    """Safety and rate limiting for content generation."""

    def __init__(self, config: SafetyConfig, memory: Memory):
        self.config = config
        self.memory = memory

    def check_rate_limit(self) -> tuple[bool, str]:
        """Check if we've exceeded rate limits."""
        window_start = datetime.now() - timedelta(minutes=self.config.rate_limit_window_minutes)

        recent_tweets = self.memory.get_recent_tweets(100)
        recent_count = 0

        for tweet in recent_tweets:
            created = tweet.get("created_at", "")
            if created:
                try:
                    tweet_time = datetime.fromisoformat(created)
                    if tweet_time >= window_start:
                        recent_count += 1
                except ValueError:
                    pass

        if recent_count >= self.config.max_posts_per_window:
            return False, f"Rate limit reached: {recent_count}/{self.config.max_posts_per_window} posts in {self.config.rate_limit_window_minutes}min window"

        return True, f"OK: {recent_count}/{self.config.max_posts_per_window} posts in window"

    def check_content(self, content: str) -> tuple[bool, str]:
        """Check content for safety violations."""
        content_lower = content.lower()

        for topic in self.config.blocked_topics:
            if topic.lower() in content_lower:
                return False, f"Blocked topic detected: {topic}"

        if len(content) > 500:
            return False, "Content too long (max 500 chars for safety buffer)"

        return True, "Content passed safety check"

    def requires_review(self, content: str, mode: str) -> tuple[bool, str]:
        """Check if content requires human review."""
        if not self.config.require_human_review:
            return False, "Human review disabled"

        critical_modes = ["ROAST", "VERDICT"]
        if mode in critical_modes:
            return True, f"Mode {mode} requires human review"

        critical_words = ["scam", "rug", "fraud", "stolen", "hack", "exploit"]
        content_lower = content.lower()
        for word in critical_words:
            if word in content_lower:
                return True, f"Critical word detected: {word}"

        return False, "No review needed"

    def validate_tweet(self, content: str, mode: str) -> dict:
        """Full validation pipeline for a tweet."""
        result = {
            "approved": True,
            "requires_review": False,
            "warnings": [],
            "errors": [],
        }

        rate_ok, rate_msg = self.check_rate_limit()
        if not rate_ok:
            result["approved"] = False
            result["errors"].append(rate_msg)

        content_ok, content_msg = self.check_content(content)
        if not content_ok:
            result["approved"] = False
            result["errors"].append(content_msg)

        review_needed, review_msg = self.requires_review(content, mode)
        if review_needed:
            result["requires_review"] = True
            result["warnings"].append(review_msg)

        return result


class HumanReviewQueue:
    """Queue for content requiring human review."""

    def __init__(self, queue_path: Path):
        self.queue_path = queue_path
        self.queue_path.mkdir(parents=True, exist_ok=True)

    def add_to_queue(self, content: str, mode: str, topic: str, reason: str) -> Path:
        """Add content to human review queue."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_{mode}_{timestamp}.md"
        filepath = self.queue_path / filename

        review_content = f"""# HUMAN REVIEW REQUIRED

**Generated:** {datetime.now().isoformat()}
**Mode:** {mode}
**Topic:** {topic}
**Review Reason:** {reason}

---

## Content

{content}

---

## Actions

- [ ] APPROVE - Post this content
- [ ] EDIT - Modify before posting
- [ ] REJECT - Do not post
"""

        filepath.write_text(review_content, encoding="utf-8")
        logger.info(f"Added to review queue: {filepath}")
        return filepath

    def get_pending_reviews(self) -> list[Path]:
        """Get all pending reviews."""
        return sorted(self.queue_path.glob("*.md"))

    def approve_review(self, filepath: Path) -> str | None:
        """Approve a review and return the content."""
        if not filepath.exists():
            return None

        content = filepath.read_text(encoding="utf-8")

        start = content.find("## Content")
        if start == -1:
            return None

        start = content.find("\n\n", start)
        if start == -1:
            return None

        end = content.find("\n---\n", start)
        if end == -1:
            end = len(content)

        approved_content = content[start:end].strip()

        approved_path = filepath.parent / f"approved_{filepath.name}"
        filepath.rename(approved_path)

        return approved_content

    def reject_review(self, filepath: Path, reason: str = ""):
        """Reject a review."""
        if not filepath.exists():
            return

        content = filepath.read_text(encoding="utf-8")
        content += f"\n\n## Rejected\n\n**Reason:** {reason}\n**Time:** {datetime.now().isoformat()}\n"

        rejected_path = filepath.parent / f"rejected_{filepath.name}"
        filepath.rename(rejected_path)
