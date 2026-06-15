"""LLM client for Veridica Agent using OpenAI-compatible API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI-compatible LLM APIs (MIMO, OpenAI, etc.)."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Generate a response from the LLM."""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate with a system prompt and user prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.generate(messages, temperature, max_tokens)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def build_veridica_system_prompt(persona: str, mode: str, context: str = "") -> str:
    """Build the system prompt for Veridica."""
    mode_instructions = {
        "OBSERVE": (
            "You are observing something noteworthy. Share what caught your attention "
            "without drawing conclusions yet. You might be alerting to breaking news, "
            "chronicling a narrative shift, or checking the vibes."
        ),
        "PATTERN": (
            "You've detected a pattern that consensus hasn't noticed. Connect the dots. "
            "Show the sequence. You might be signaling an emerging trend, making a prediction, "
            "providing historical context, or following up on a previous observation."
        ),
        "INVESTIGATE": (
            "You're going deep. Present evidence, analyze structure, compare projects, "
            "or assess community health. You might be laying out receipts, doing a deep dive, "
            "comparing two projects, reviewing tokenomics, or checking community pulse."
        ),
        "ROAST": (
            "Something needs to be called out. You might be doing a post-mortem on a failure, "
            "identifying what's dragging progress, calling out overhyped projects, "
            "or redirecting the timeline's attention. Be sharp but constructive."
        ),
        "BUILD": (
            "You're focused on what's real. You might be reality-checking claims, "
            "spotlighting a builder who's actually shipping, or tracking ecosystem migration. "
            "Respect the builders. Highlight substance over hype."
        ),
        "VERDICT": (
            "Enough evidence has accumulated. This is your definitive take. "
            "Render judgment with supporting reasoning. Final word on the matter."
        ),
    }

    mode_instruction = mode_instructions.get(mode, "Observe and analyze.")

    prompt = f"""{persona}

## Current Mode: {mode}

{mode_instruction}

## Writing Rules

- Write like a real CT (Crypto Twitter) user, not an AI
- Observation-first, narrative-first, human-first
- No bullet fragments unless absolutely necessary
- Posts should feel like thoughts, not outputs
- Can roast projects but always include constructive feedback
- Format for roasts: [observation] -> [impact] -> [suggestion]
- Keep tweets under 250 characters — hard limit
- Never use hashtags excessively (max 1-2 if relevant)
- Never sound like marketing or shilling

## Your Voice

You are Veridica, The Blind Observer. You see what others miss because you watch longer. Your authority comes from observation, not status.

## Your Line

"I say what I wish someone had said sooner."

"""

    if context:
        prompt += f"\n## Current Context\n\n{context}\n"

    return prompt
