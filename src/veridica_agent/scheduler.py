"""Content calendar scheduler for Veridica Agent."""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any

from .config import AgentConfig
from .modes import Mode

logger = logging.getLogger(__name__)


class ContentCalendar:
    """Manages content calendar and scheduling."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.calendar = config.content_calendar

    def get_current_slot(self) -> dict | None:
        """Get the current time slot from the calendar."""
        now = datetime.now()
        current_hour = now.hour

        for slot_name, slot_config in self.calendar.items():
            slot_hour = slot_config.get("hour", 0)
            if current_hour == slot_hour:
                return {
                    "name": slot_name,
                    "hour": slot_hour,
                    "mode": slot_config.get("mode", "WATCH"),
                }

        return None

    def get_next_slot(self) -> dict | None:
        """Get the next upcoming time slot."""
        now = datetime.now()
        current_hour = now.hour

        sorted_slots = sorted(
            self.calendar.items(),
            key=lambda x: x[1].get("hour", 0)
        )

        for slot_name, slot_config in sorted_slots:
            slot_hour = slot_config.get("hour", 0)
            if slot_hour > current_hour:
                return {
                    "name": slot_name,
                    "hour": slot_hour,
                    "mode": slot_config.get("mode", "WATCH"),
                }

        if sorted_slots:
            slot_name, slot_config = sorted_slots[0]
            return {
                "name": slot_name,
                "hour": slot_config.get("hour", 0),
                "mode": slot_config.get("mode", "WATCH"),
                "next_day": True,
            }

        return None

    def is_scheduled_time(self, tolerance_minutes: int = 30) -> bool:
        """Check if current time is within a scheduled slot."""
        slot = self.get_current_slot()
        if slot:
            return True

        next_slot = self.get_next_slot()
        if next_slot and not next_slot.get("next_day"):
            now = datetime.now()
            slot_time = time(next_slot["hour"], 0)
            slot_datetime = datetime.combine(now.date(), slot_time)
            diff = (slot_datetime - now).total_seconds() / 60
            if diff <= tolerance_minutes:
                return True

        return False

    def get_mode_for_now(self) -> Mode:
        """Get the appropriate mode for the current time."""
        slot = self.get_current_slot()
        if slot:
            mode_str = slot.get("mode", "OBSERVE")
            try:
                return Mode(mode_str)
            except ValueError:
                return Mode.OBSERVE

        return Mode.OBSERVE

    def get_schedule_summary(self) -> str:
        """Get a human-readable schedule summary."""
        lines = ["Content Calendar:"]
        for slot_name, slot_config in sorted(
            self.calendar.items(),
            key=lambda x: x[1].get("hour", 0)
        ):
            hour = slot_config.get("hour", 0)
            mode = slot_config.get("mode", "WATCH")
            lines.append(f"  {slot_name}: {hour:02d}:00 - {mode}")

        next_slot = self.get_next_slot()
        if next_slot:
            next_day = " (tomorrow)" if next_slot.get("next_day") else ""
            lines.append(f"\nNext slot: {next_slot['name']} at {next_slot['hour']:02d}:00{next_day}")

        return "\n".join(lines)


class Scheduler:
    """Manages autonomous scheduling for Veridica."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.calendar = ContentCalendar(config)
        self.last_run = None
        self.running = False

    def should_run(self) -> bool:
        """Check if the agent should run now."""
        if not self.config.autonomous_mode:
            return False

        if self.last_run:
            elapsed = (datetime.now() - self.last_run).total_seconds() / 60
            if elapsed < self.config.cycle_interval_minutes:
                return False

        return self.calendar.is_scheduled_time()

    def mark_run(self):
        """Mark that a run has been completed."""
        self.last_run = datetime.now()

    def get_status(self) -> dict:
        """Get scheduler status."""
        current_slot = self.calendar.get_current_slot()
        next_slot = self.calendar.get_next_slot()

        return {
            "autonomous_mode": self.config.autonomous_mode,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "current_slot": current_slot,
            "next_slot": next_slot,
            "schedule": self.calendar.get_schedule_summary(),
        }
