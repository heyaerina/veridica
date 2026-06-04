"""GitHub signal source — developer activity tracking (FREE, no API key needed)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

from .base import Signal, SignalSource, SignalType

logger = logging.getLogger(__name__)


class GitHubSource(SignalSource):
    """Tracks GitHub developer activity for crypto/Web3 projects."""

    name = "github"
    BASE_URL = "https://api.github.com"

    # Crypto/Web3 repos to track
    WATCHED_REPOS = [
        # L1/L2
        ("ethereum", "go-ethereum"),       # Geth
        ("ethereum", "consensus-specs"),    # ETH2 specs
        ("bitcoin", "bitcoin"),             # Bitcoin Core
        ("solana-labs", "solana"),          # Solana
        ("base", "node"),                   # Base
        ("OffchainLabs", "nitro"),          # Arbitrum
        ("matter-labs", "zksync-era"),      # zkSync

        # DeFi
        ("Uniswap", "v3-core"),            # Uniswap
        ("aave", "aave-v3-core"),          # Aave

        # Infra
        ("ipfs", "kubo"),                  # IPFS
        ("smartcontractkit", "chainlink"), # Chainlink

        # Agentic / AI
        ("OpenZeppelin", "openzeppelin-contracts"),  # OpenZeppelin
        ("Vectorized", "solady"),                     # Solady
    ]

    # Trending search queries for crypto repos
    TRENDING_QUERIES = [
        "language:solidity stars:>100 pushed:>2026-05-28",
        "topic:web3 stars:>50 pushed:>2026-05-28",
        "topic:defi stars:>50 pushed:>2026-05-28",
        "topic:ai-agent stars:>30 pushed:>2026-05-28",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Veridica-Agent/2.0",
            },
        )

    async def poll(self) -> list[Signal]:
        """Poll GitHub for developer activity signals."""
        signals: list[Signal] = []

        import asyncio
        results = await asyncio.gather(
            self._poll_watched_repos(),
            self._poll_trending_repos(),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"GitHub poll error: {result}")
            elif isinstance(result, list):
                signals.extend(result)

        return signals

    async def _poll_watched_repos(self) -> list[Signal]:
        """Check recent activity on watched repos."""
        signals = []

        for owner, repo in self.WATCHED_REPOS:
            try:
                # Get recent commits
                resp = await self.client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/commits",
                    params={"per_page": 5},
                    headers={"X-GitHub-Api-Version": "2022-11-28"},
                )

                if resp.status_code == 403:
                    # Rate limited
                    logger.debug(f"GitHub rate limited for {owner}/{repo}")
                    break

                resp.raise_for_status()
                commits = resp.json()

                if not commits:
                    continue

                # Count commits in last 24h
                now = datetime.now()
                recent_commits = []
                for commit in commits:
                    date_str = commit.get("commit", {}).get("committer", {}).get("date", "")
                    if date_str:
                        try:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                            if (now - dt).total_seconds() < 86400:  # 24h
                                recent_commits.append(commit)
                        except Exception:
                            pass

                if len(recent_commits) >= 3:
                    # High activity: 3+ commits in 24h
                    signals.append(Signal(
                        source="github",
                        signal_type=SignalType.GITHUB_ACTIVITY,
                        title=f"{owner}/{repo}: {len(recent_commits)} commits in 24h",
                        content=f"Active development on {owner}/{repo}. Latest: {commits[0].get('commit', {}).get('message', '')[:100]}",
                        url=f"https://github.com/{owner}/{repo}",
                        topics=[repo, owner, "Development"],
                        metadata={
                            "owner": owner,
                            "repo": repo,
                            "commit_count_24h": len(recent_commits),
                            "latest_commit": commits[0].get("sha", "")[:8],
                            "latest_message": commits[0].get("commit", {}).get("message", "")[:200],
                        },
                        confidence=0.8,
                        urgency=5,
                    ))

                elif len(recent_commits) >= 1:
                    # Normal activity
                    signals.append(Signal(
                        source="github",
                        signal_type=SignalType.GITHUB_ACTIVITY,
                        title=f"{owner}/{repo}: active development",
                        content=f"Latest commit: {commits[0].get('commit', {}).get('message', '')[:100]}",
                        url=f"https://github.com/{owner}/{repo}",
                        topics=[repo, owner, "Development"],
                        metadata={
                            "owner": owner,
                            "repo": repo,
                            "commit_count_24h": len(recent_commits),
                            "latest_commit": commits[0].get("sha", "")[:8],
                        },
                        confidence=0.7,
                        urgency=3,
                    ))

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.debug("GitHub API rate limited, stopping watched repos")
                    break
                logger.warning(f"GitHub API error for {owner}/{repo}: {e.response.status_code}")
            except Exception as e:
                logger.warning(f"GitHub fetch failed for {owner}/{repo}: {e}")

        return signals

    async def _poll_trending_repos(self) -> list[Signal]:
        """Search for trending crypto-related repos."""
        signals = []

        for query in self.TRENDING_QUERIES[:2]:  # Limit to conserve rate limit
            try:
                resp = await self.client.get(
                    f"{self.BASE_URL}/search/repositories",
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 5,
                    },
                )

                if resp.status_code == 403:
                    logger.debug("GitHub search rate limited")
                    break

                resp.raise_for_status()
                data = resp.json()
                repos = data.get("items", [])

                for repo in repos[:3]:
                    name = repo.get("full_name", "")
                    stars = repo.get("stargazers_count", 0)
                    description = repo.get("description", "") or ""
                    language = repo.get("language", "")
                    updated_at = repo.get("updated_at", "")
                    topics = repo.get("topics", [])

                    signals.append(Signal(
                        source="github",
                        signal_type=SignalType.GITHUB_ACTIVITY,
                        title=f"Trending repo: {name} ({stars} stars)",
                        content=f"{description[:200]}",
                        url=repo.get("html_url", ""),
                        topics=[repo.get("name", ""), language] + topics[:3],
                        metadata={
                            "full_name": name,
                            "stars": stars,
                            "language": language,
                            "description": description[:300],
                            "updated_at": updated_at,
                            "topics": topics,
                        },
                        confidence=0.7,
                        urgency=4,
                    ))

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    break
                logger.warning(f"GitHub search error: {e.response.status_code}")
            except Exception as e:
                logger.warning(f"GitHub search failed: {e}")

        return signals

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
