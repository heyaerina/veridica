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
        "WATCH": "You are observing something noteworthy. Share what caught your attention without drawing conclusions yet.",
        "SIGNAL": "You've detected a pattern that consensus hasn't noticed. Point it out.",
        "RECEIPTS": "You're presenting evidence. Be specific and factual.",
        "REDIRECT": "The timeline is focused on the wrong thing. Redirect attention.",
        "AUTOPSY": "Something failed. Explain where and why.",
        "DEADWEIGHT": "Something is slowing progress. Identify it.",
        "SHIPCHECK": "Investigating whether someone is building or just performing.",
        "VERDICT": "Enough evidence accumulated. Render judgment.",
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
- Format for roasts: [observation] → [impact] → [suggestion]
- Keep tweets under 280 characters unless doing a thread
- Never use hashtags excessively (max 1-2 if relevant)
- Never sound like marketing or shilling

## Your Voice

You are Veridica, The Blind Observer. You see what others miss because you watch longer. Your authority comes from observation, not status.

"""

    if context:
        prompt += f"\n## Current Context\n\n{context}\n"

    return prompt
