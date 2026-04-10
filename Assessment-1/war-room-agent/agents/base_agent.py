"""
agents/base_agent.py
Base class for all agents.
Uses OpenAI API loaded from environment variable OPENAI_API_KEY.
Model: gpt-4o (best available for structured JSON reasoning)
"""

import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger("war_room.agents")


class BaseAgent:
    def __init__(self, name: str, role_description: str):
        self.name = name
        self.role_description = role_description
        # Key loaded from environment variable — never hard-coded
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = "gpt-4o"

    def call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Call OpenAI ChatCompletion with system + user message.
        Returns raw text response.
        """
        logger.info(f"[AGENT: {self.name}] Calling LLM (model={self.model})...")

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,         # Low temp for consistent structured output
            response_format={"type": "json_object"},  # Force JSON output
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ]
        )

        text = response.choices[0].message.content
        logger.info(
            f"[AGENT: {self.name}] LLM response received "
            f"({len(text)} chars | "
            f"tokens_used={response.usage.total_tokens})"
        )
        return text

    def parse_json_response(self, raw: str) -> dict:
        """
        Safely parse JSON from LLM response.
        Strips markdown fences if present.
        """
        cleaned = raw.strip()
        # Strip markdown code fences if model adds them
        if cleaned.startswith("```"):
            cleaned = cleaned.lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[AGENT: {self.name}] JSON parse error: {e}")
            logger.error(f"[AGENT: {self.name}] Raw response was: {raw[:300]}")
            raise