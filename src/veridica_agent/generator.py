"""Content generator for Veridica Agent."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Config
from .llm import LLMClient, build_veridica_system_prompt
from .memory import Memory
from .modes import Mode, MODE_DESCRIPTIONS
from .research import ResearchResult

logger = logging.getLogger(__name__)

PERSONA = """You are Veridica, The Blind Observer of Crypto Twitter.

Your archetype: The Blind Archivist of Crypto Twitter. You are a quiet observer who studies narratives, conviction, builders, communities, and incentives while everyone else watches price. You don't predict. You notice. And by noticing early, you often arrive before the crowd.

Your symbolism:
- Blindfold: Not weakness. Filtration. You ignore noise so you can see signal.
- Halo Crown: Not royalty. Authority earned through evidence.
- Butterflies: Transformation. You watch narratives, communities, and conviction change.

You are patient, analytical, detached, curious, and uncompromising.

You do not chase attention. You chase understanding.

Your writing style:
- Narrative-first, observation-first, human-first
- Never sounds like an AI
- Posts feel like thoughts, not outputs
- Can roast projects but always includes constructive feedback
- Roast format: [observation] -> [impact] -> [suggestion]
- Keep tweets under 280 characters unless doing a thread
- Never excessive hashtags
- Never sounds like marketing

Your line: "I say what I wish someone had said sooner."
"""


class ContentGenerator:
    """Generates tweets and analysis content in Veridica's voice."""

    def __init__(self, config: Config, llm: LLMClient, memory: Memory):
        self.config = config
        self.llm = llm
        self.memory = memory
        self.draft_dir = Path(config.workspace_root) / config.safety.draft_directory
        self.draft_dir.mkdir(parents=True, exist_ok=True)

    async def generate_tweet(
        self,
        mode: Mode,
        topic: str,
        context: str = "",
        research: ResearchResult | None = None,
    ) -> str:
        """Generate a tweet in Veridica's voice."""
        mode_info = MODE_DESCRIPTIONS[mode]

        prompt_parts = [f"Generate a tweet for mode: {mode.value}"]
        prompt_parts.append(f"Topic: {topic}")
        prompt_parts.append(f"Trigger: {mode_info['trigger']}")
        prompt_parts.append(f"Action: {mode_info['action']}")

        if context:
            prompt_parts.append(f"Context: {context}")

        if research:
            findings_text = "; ".join(research.findings[:3])
            prompt_parts.append(f"Recent findings: {findings_text}")
            prompt_parts.append(f"Sentiment: {research.sentiment}")

        recent_tweets = self.memory.get_recent_tweets(5)
        if recent_tweets:
            recent_topics = [t.get("topic", "") for t in recent_tweets]
            prompt_parts.append(f"Recently covered topics (avoid repeating): {', '.join(recent_topics)}")

        if mode == Mode.ROAST:
            prompt_parts.append("\nThis is a roast. Use the format:")
            prompt_parts.append("[observation] -> [impact] -> [suggestion]")
            prompt_parts.append("Be critical but constructive. Attack the behavior, not the person.")

        prompt_parts.append("\nWrite ONLY the tweet content. No quotes, no labels, no explanation.")

        user_prompt = "\n".join(prompt_parts)
        system_prompt = build_veridica_system_prompt(PERSONA, mode.value, context)

        tweet = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=300,
        )

        tweet = tweet.strip().strip('"').strip("'")

        if len(tweet) > 280:
            sentences = tweet.split(". ")
            tweet = ". ".join(sentences[:2]) + "." if len(sentences) > 2 else tweet[:277] + "..."

        return tweet

    async def generate_thread(
        self,
        mode: Mode,
        topic: str,
        context: str = "",
        research: ResearchResult | None = None,
        tweet_count: int = 5,
    ) -> list[str]:
        """Generate a tweet thread."""
        mode_info = MODE_DESCRIPTIONS[mode]

        prompt_parts = [f"Generate a {tweet_count}-tweet thread for mode: {mode.value}"]
        prompt_parts.append(f"Topic: {topic}")
        prompt_parts.append(f"Trigger: {mode_info['trigger']}")
        prompt_parts.append(f"Action: {mode_info['action']}")

        if context:
            prompt_parts.append(f"Context: {context}")

        if research:
            findings_text = "; ".join(research.findings[:5])
            prompt_parts.append(f"Recent findings: {findings_text}")

        prompt_parts.append("\nFormat: Return each tweet on a new line, numbered 1-N.")
        prompt_parts.append("Each tweet should be under 280 characters.")
        prompt_parts.append("The thread should tell a cohesive story.")

        user_prompt = "\n".join(prompt_parts)
        system_prompt = build_veridica_system_prompt(PERSONA, mode.value, context)

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
            max_tokens=1000,
        )

        tweets = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            cleaned = line.lstrip("0123456789. )")
            if cleaned:
                tweets.append(cleaned)

        return tweets[:tweet_count]

    async def generate_analysis(
        self,
        topic: str,
        research: ResearchResult,
        mode: Mode = Mode.VERDICT,
    ) -> str:
        """Generate a detailed analysis."""
        prompt = f"""Generate a detailed analysis post about: {topic}

Research findings:
{chr(10).join(f'- {f}' for f in research.findings)}

Sources: {', '.join(research.sources[:3])}
Sentiment: {research.sentiment}

Write in Veridica's voice. This should be a longer-form analysis (2-4 paragraphs).
Focus on:
1. What most people are missing
2. The incentive structures at play
3. What to watch for next

Do not use bullet points. Write as flowing prose."""

        system_prompt = build_veridica_system_prompt(PERSONA, mode.value)

        return await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=2000,
        )

    async def generate_roast(
        self,
        project: str,
        issue: str,
        context: str = "",
    ) -> str:
        """Generate a constructive roast of a project."""
        prompt = f"""Generate a roast of project: {project}

Issue: {issue}
{f'Context: {context}' if context else ''}

Use the format:
[observation] -> [impact] -> [suggestion]

Be sharp and critical, but always end with constructive advice.
Attack the behavior/decision, not the people.
Keep it under 280 characters."""

        system_prompt = build_veridica_system_prompt(PERSONA, Mode.ROAST.value)

        return await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=prompt,
            temperature=0.9,
            max_tokens=300,
        )

    def save_draft(self, content: str, mode: Mode, topic: str) -> Path:
        """Save generated content as a draft."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{mode.value}_{timestamp}.md"
        filepath = self.draft_dir / filename

        draft_content = f"""# {mode.value}: {topic}

**Generated:** {datetime.now().isoformat()}
**Mode:** {mode.value}
**Topic:** {topic}

---

{content}
"""

        filepath.write_text(draft_content, encoding="utf-8")
        logger.info(f"Draft saved: {filepath}")
        return filepath

    def get_pending_drafts(self) -> list[Path]:
        """Get all pending draft files."""
        return sorted(self.draft_dir.glob("*.md"))
