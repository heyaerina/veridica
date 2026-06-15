"""Snapshot signal source — FREE DAO governance data.

Snapshot provides off-chain voting data for DAOs.
Free tier: GraphQL API, no key required.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class SnapshotSource(SignalSource):
    """Fetches DAO governance data from Snapshot (free, no key)."""

    name = "snapshot"
    GRAPHQL_URL = "https://hub.snapshot.org/graphql"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Veridica/2.0"},
        )

    async def poll(self) -> list[Signal]:
        """Poll Snapshot for governance signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_active_proposals(),
            self._poll_ending_soon(),
            self._poll_high_turnout(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Snapshot poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_active_proposals(self) -> list[Signal]:
        """Fetch active governance proposals from major DAOs."""
        signals = []
        try:
            query = """
            query {
                proposals(
                    first: 20,
                    where: {state: "active"},
                    orderBy: "created",
                    orderDirection: desc
                ) {
                    id
                    title
                    body
                    choices
                    start
                    end
                    state
                    space {
                        id
                        name
                        members
                    }
                    scores_total
                    votes
                }
            }
            """
            resp = await self.client.post(
                self.GRAPHQL_URL,
                json={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()

            proposals = data.get("data", {}).get("proposals", [])
            now = datetime.now()

            for prop in proposals:
                title = prop.get("title", "")
                space = prop.get("space", {})
                space_name = space.get("name", space.get("id", ""))
                votes = prop.get("votes", 0)
                scores_total = prop.get("scores_total", 0)
                end_ts = prop.get("end", 0)

                try:
                    end_date = datetime.fromtimestamp(end_ts)
                    hours_left = (end_date - now).total_seconds() / 3600
                except (ValueError, TypeError):
                    hours_left = 0

                # High-engagement proposals
                if votes > 100:
                    signals.append(Signal(
                        source="snapshot",
                        signal_type=SignalType.DAO_PROPOSAL,
                        title=f"[{space_name}] {title}",
                        content=f"Active proposal in {space_name}: {title}. "
                                f"Votes: {votes:,}. "
                                f"Hours remaining: {hours_left:.0f}",
                        url=f"https://snapshot.org/#/{space.get('id', '')}/proposal/{prop.get('id', '')}",
                        topics=[space_name, "Governance", "DAO"],
                        metadata={
                            "space": space_name,
                            "proposal_id": prop.get("id", ""),
                            "votes": votes,
                            "scores_total": scores_total,
                            "hours_remaining": hours_left,
                        },
                        confidence=0.85,
                        urgency=6,
                    ))

        except Exception as e:
            logger.warning(f"Snapshot active proposals poll failed: {e}")

        return signals

    async def _poll_ending_soon(self) -> list[Signal]:
        """Find proposals ending within 24 hours."""
        signals = []
        try:
            now_ts = int(datetime.now().timestamp())
            day_from_now = now_ts + 86400

            query = """
            query($end: Int!, $endMax: Int!) {
                proposals(
                    first: 20,
                    where: {
                        state: "active",
                        end_gt: $end,
                        end_lt: $endMax
                    },
                    orderBy: "end",
                    orderDirection: asc
                ) {
                    id
                    title
                    end
                    space {
                        id
                        name
                    }
                    votes
                    scores_total
                }
            }
            """
            resp = await self.client.post(
                self.GRAPHQL_URL,
                json={
                    "query": query,
                    "variables": {"end": now_ts, "endMax": day_from_now},
                },
            )
            resp.raise_for_status()
            data = resp.json()

            proposals = data.get("data", {}).get("proposals", [])
            now = datetime.now()

            for prop in proposals:
                title = prop.get("title", "")
                space = prop.get("space", {})
                space_name = space.get("name", "")
                votes = prop.get("votes", 0)
                end_ts = prop.get("end", 0)

                try:
                    end_date = datetime.fromtimestamp(end_ts)
                    hours_left = (end_date - now).total_seconds() / 3600
                except (ValueError, TypeError):
                    hours_left = 0

                signals.append(Signal(
                    source="snapshot",
                    signal_type=SignalType.VOTE_ENDING,
                    title=f"ENDING SOON: [{space_name}] {title} ({hours_left:.0f}h left)",
                    content=f"Proposal in {space_name} ending in {hours_left:.0f} hours: {title}. "
                            f"Current votes: {votes:,}. "
                            f"Last chance to vote.",
                    url=f"https://snapshot.org/#/{space.get('id', '')}/proposal/{prop.get('id', '')}",
                    topics=[space_name, "Governance", "Ending Soon"],
                    metadata={
                        "space": space_name,
                        "proposal_id": prop.get("id", ""),
                        "votes": votes,
                        "hours_remaining": hours_left,
                    },
                    confidence=0.9,
                    urgency=7,
                ))

        except Exception as e:
            logger.warning(f"Snapshot ending soon poll failed: {e}")

        return signals

    async def _poll_high_turnout(self) -> list[Signal]:
        """Detect proposals with unusually high voter turnout."""
        signals = []
        try:
            query = """
            query {
                proposals(
                    first: 10,
                    where: {state: "closed"},
                    orderBy: "votes",
                    orderDirection: desc
                ) {
                    id
                    title
                    space {
                        id
                        name
                        members
                    }
                    votes
                    scores_total
                    state
                }
            }
            """
            resp = await self.client.post(
                self.GRAPHQL_URL,
                json={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()

            proposals = data.get("data", {}).get("proposals", [])

            for prop in proposals:
                title = prop.get("title", "")
                space = prop.get("space", {})
                space_name = space.get("name", "")
                members = space.get("members", 0)
                votes = prop.get("votes", 0)

                # High participation (>10% of members)
                if members and votes and votes > members * 0.1:
                    participation = (votes / members) * 100
                    signals.append(Signal(
                        source="snapshot",
                        signal_type=SignalType.DAO_PROPOSAL,
                        title=f"HIGH TURNOUT: [{space_name}] {title} ({participation:.0f}% participation)",
                        content=f"{space_name} proposal had {participation:.0f}% participation "
                                f"({votes:,} votes from {members:,} members). "
                                f"This level of engagement is notable.",
                        url=f"https://snapshot.org/#/{space.get('id', '')}/proposal/{prop.get('id', '')}",
                        topics=[space_name, "High Turnout", "Governance"],
                        metadata={
                            "space": space_name,
                            "votes": votes,
                            "members": members,
                            "participation": participation,
                        },
                        confidence=0.8,
                        urgency=5,
                    ))

        except Exception as e:
            logger.warning(f"Snapshot high turnout poll failed: {e}")

        return signals

    async def close(self):
        await self.client.aclose()
