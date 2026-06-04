"""Draft manager — handles draft creation, review workflow, and status tracking."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Draft:
    """A content draft with metadata and status."""

    id: str
    content: str
    mode: str
    topic: str
    trigger: str = "schedule"      # "event", "schedule", "signal"
    event_type: str = ""
    confidence: float = 0.5
    status: str = "pending_review"  # pending_review → approved → posted / rejected
    generated_at: str = ""
    reviewed_at: str | None = None
    rejection_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class DraftManager:
    """Manages content drafts with review workflow."""

    def __init__(self, draft_dir: Path, review_dir: Path):
        self.draft_dir = Path(draft_dir)
        self.review_dir = Path(review_dir)
        self.draft_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def create_draft(
        self,
        content: str,
        mode: str,
        topic: str,
        trigger: str = "schedule",
        event_type: str = "",
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> Draft:
        """Create a new draft."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_id = f"{mode}_{timestamp}"

        draft = Draft(
            id=draft_id,
            content=content,
            mode=mode,
            topic=topic,
            trigger=trigger,
            event_type=event_type,
            confidence=confidence,
            status="pending_review",
            generated_at=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        # Save as markdown for human readability
        md_path = self.draft_dir / f"{draft_id}.md"
        md_content = self._render_markdown(draft)
        md_path.write_text(md_content, encoding="utf-8")

        # Save as JSON for programmatic access
        json_path = self.draft_dir / f"{draft_id}.json"
        json_path.write_text(json.dumps(draft.to_dict(), indent=2), encoding="utf-8")

        logger.info(f"Draft created: {draft_id}")
        return draft

    def get_pending_drafts(self) -> list[Draft]:
        """Get all drafts pending review."""
        drafts = []
        for json_file in sorted(self.draft_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if data.get("status") == "pending_review":
                    drafts.append(Draft(**data))
            except Exception as e:
                logger.warning(f"Failed to load draft {json_file}: {e}")
        return drafts

    def get_draft(self, draft_id: str) -> Draft | None:
        """Get a specific draft by ID."""
        json_path = self.draft_dir / f"{draft_id}.json"
        if not json_path.exists():
            return None
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return Draft(**data)
        except Exception:
            return None

    def approve_draft(self, draft_id: str) -> Draft | None:
        """Approve a draft for posting."""
        draft = self.get_draft(draft_id)
        if not draft:
            return None

        draft.status = "approved"
        draft.reviewed_at = datetime.now().isoformat()

        # Update JSON
        json_path = self.draft_dir / f"{draft_id}.json"
        json_path.write_text(json.dumps(draft.to_dict(), indent=2), encoding="utf-8")

        # Update markdown
        md_path = self.draft_dir / f"{draft_id}.md"
        md_path.write_text(self._render_markdown(draft), encoding="utf-8")

        logger.info(f"Draft approved: {draft_id}")
        return draft

    def reject_draft(self, draft_id: str, reason: str = "") -> Draft | None:
        """Reject a draft."""
        draft = self.get_draft(draft_id)
        if not draft:
            return None

        draft.status = "rejected"
        draft.reviewed_at = datetime.now().isoformat()
        draft.rejection_reason = reason

        # Update JSON
        json_path = self.draft_dir / f"{draft_id}.json"
        json_path.write_text(json.dumps(draft.to_dict(), indent=2), encoding="utf-8")

        # Update markdown
        md_path = self.draft_dir / f"{draft_id}.md"
        md_path.write_text(self._render_markdown(draft), encoding="utf-8")

        logger.info(f"Draft rejected: {draft_id} — {reason}")
        return draft

    def mark_posted(self, draft_id: str) -> Draft | None:
        """Mark a draft as posted."""
        draft = self.get_draft(draft_id)
        if not draft:
            return None

        draft.status = "posted"

        json_path = self.draft_dir / f"{draft_id}.json"
        json_path.write_text(json.dumps(draft.to_dict(), indent=2), encoding="utf-8")

        logger.info(f"Draft marked as posted: {draft_id}")
        return draft

    def get_all_drafts(self, status: str | None = None) -> list[Draft]:
        """Get all drafts, optionally filtered by status."""
        drafts = []
        for json_file in sorted(self.draft_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if status is None or data.get("status") == status:
                    drafts.append(Draft(**data))
            except Exception as e:
                logger.warning(f"Failed to load draft {json_file}: {e}")
        return drafts

    def get_stats(self) -> dict[str, Any]:
        """Get draft statistics."""
        all_drafts = self.get_all_drafts()
        status_counts = {}
        trigger_counts = {}
        mode_counts = {}

        for d in all_drafts:
            status_counts[d.status] = status_counts.get(d.status, 0) + 1
            trigger_counts[d.trigger] = trigger_counts.get(d.trigger, 0) + 1
            mode_counts[d.mode] = mode_counts.get(d.mode, 0) + 1

        return {
            "total_drafts": len(all_drafts),
            "by_status": status_counts,
            "by_trigger": trigger_counts,
            "by_mode": mode_counts,
        }

    def _render_markdown(self, draft: Draft) -> str:
        """Render a draft as markdown for human readability."""
        status_emoji = {
            "pending_review": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "posted": "📤",
        }
        emoji = status_emoji.get(draft.status, "❓")

        lines = [
            f"# {emoji} {draft.mode}: {draft.topic}",
            "",
            f"**ID:** {draft.id}",
            f"**Generated:** {draft.generated_at}",
            f"**Mode:** {draft.mode}",
            f"**Topic:** {draft.topic}",
            f"**Trigger:** {draft.trigger}",
            f"**Confidence:** {draft.confidence:.0%}",
            f"**Status:** {draft.status}",
        ]

        if draft.event_type:
            lines.append(f"**Event Type:** {draft.event_type}")

        if draft.reviewed_at:
            lines.append(f"**Reviewed:** {draft.reviewed_at}")

        if draft.rejection_reason:
            lines.append(f"**Rejection Reason:** {draft.rejection_reason}")

        lines.extend([
            "",
            "---",
            "",
            "## Content",
            "",
            draft.content,
            "",
            "---",
            "",
            "## Actions",
            "",
        ])

        if draft.status == "pending_review":
            lines.extend([
                "- [ ] APPROVE — Post this content",
                "- [ ] EDIT — Modify before posting",
                "- [ ] REJECT — Do not post",
            ])
        elif draft.status == "approved":
            lines.append("- [x] APPROVED — Ready to post")
        elif draft.status == "rejected":
            lines.append(f"- [x] REJECTED — {draft.rejection_reason}")

        return "\n".join(lines)
