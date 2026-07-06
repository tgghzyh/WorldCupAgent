"""LLM Integration Module — WC2026 Agent Reasoning Engine.

This module provides LLM-powered reasoning for the World Cup Prediction Agent.
It uses Ali Cloud Dashscope (OpenAI-compatible API) to:

1. Analyze match results and explain implications
2. Generate reasoning about team performance
3. Provide narrative context for predictions
4. Summarize tournament state

Usage:
  from worldcup_agent.prediction.llm_engine import LLMEngine
  engine = LLMEngine()
  result = await engine.analyze_match(home_team, away_team, result, world_state)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

import httpx

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── Configuration ─────────────────────────────────────────────────────────────

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
API_HOST = os.environ.get("DASHSCOPE_API_HOST", "ws-vynwkc75868qxurp.cn-beijing.maas.aliyuncs.com")
API_BASE = os.environ.get("OPENAI_API_BASE", "https://ws-vynwkc75868qxurp.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")


# ── LLM Result Types ────────────────────────────────────────────────────────────

@dataclass
class LLMResult:
    """Result from LLM inference."""
    content: str
    model: str
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None


# ── LLM Engine ─────────────────────────────────────────────────────────────────

class LLMEngine:
    """
    LLM-powered reasoning engine for World Cup predictions.

    Uses Ali Cloud Dashscope (OpenAI-compatible API) to provide:
    - Match result analysis
    - Team performance reasoning
    - Prediction explanations
    - Tournament narrative generation
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or API_KEY
        self.api_base = api_base or API_BASE
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("API key not provided. Set DASHSCOPE_API_KEY in .env file.")

    def _make_request(self, messages: list[dict], **kwargs) -> LLMResult:
        """Make a request to the LLM API."""
        import time
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                return LLMResult(
                    content=content,
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    latency_ms=latency_ms,
                    success=True,
                )

        except httpx.HTTPStatusError as e:
            return LLMResult(
                content="",
                model=self.model,
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                latency_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return LLMResult(
                content="",
                model=self.model,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    def chat(self, prompt: str, system: str | None = None, **kwargs) -> LLMResult:
        """Simple chat completion."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return self._make_request(messages, **kwargs)

    def analyze_match_result(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        world_state_context: dict | None = None,
    ) -> LLMResult:
        """
        Analyze a match result and provide reasoning.

        Returns explanation of what this result means for both teams.
        """
        system_prompt = """You are an expert football analyst for the World Cup.
You analyze match results and explain their implications for the tournament.
Provide concise, insightful analysis in 2-3 sentences."""

        winner = home_team if home_score > away_score else away_team if away_score > home_score else None
        score_str = f"{home_score}-{away_score}"

        if winner:
            loser = away_team if winner == home_team else home_team
            prompt = f"""Analyze this World Cup result:

{home_team} {score_str} {away_team}

What does this result mean for {winner}'s tournament prospects?
What challenges does {loser} face going forward?
Consider the context: {world_state_context or 'No additional context'}"""
        else:
            prompt = f"""Analyze this World Cup draw:

{home_team} {score_str} {away_team}

How does this draw affect both teams' qualification chances?
What do they need in their remaining matches?
Consider the context: {world_state_context or 'No additional context'}"""

        return self.chat(prompt, system=system_prompt, temperature=0.7, max_tokens=300)

    def generate_prediction_explanation(
        self,
        home_team: str,
        away_team: str,
        home_win_prob: float,
        draw_prob: float,
        away_win_prob: float,
        factors: list[dict] | None = None,
    ) -> LLMResult:
        """
        Generate a natural language explanation of a prediction.

        Makes the prediction more accessible to users.
        """
        system_prompt = """You are a friendly football analyst explaining AI predictions.
Make probabilities accessible and engaging. Use concrete examples.
Keep explanations to 2-3 sentences max."""

        factors_str = ""
        if factors:
            factors_str = "\nKey factors:\n" + "\n".join(
                f"- {f.get('name', 'Factor')}: {f.get('evidence', '')}"
                for f in factors[:3]
            )

        prompt = f"""Explain this World Cup match prediction in plain English:

{home_team} vs {away_team}

Probabilities:
- {home_team} wins: {home_win_prob:.1%}
- Draw: {draw_prob:.1%}
- {away_team} wins: {away_win_prob:.1%}

{factors_str}

Provide a brief, engaging explanation of why this prediction makes sense."""

        return self.chat(prompt, system=system_prompt, temperature=0.5, max_tokens=200)

    def summarize_tournament_state(self, world_state: dict) -> LLMResult:
        """
        Generate a narrative summary of the current tournament state.

        Creates an engaging summary for the daily briefing.
        """
        system_prompt = """You are a charismatic World Cup commentator creating a daily briefing.
Make it engaging, highlight key storylines, and build anticipation.
Keep it punchy and memorable - 3-4 sentences max."""

        # Extract key info from world state
        results = world_state.get("results", [])
        teams = world_state.get("teams", {})

        # Get top performers
        top_teams = []
        for name, data in list(teams.items())[:5]:
            if data.get("stats", {}).get("played", 0) > 0:
                top_teams.append(f"{name} ({data.get('stats', {}).get('points', 0)}pts)")

        results_summary = f"{len(results)} matches completed"
        top_performers = ", ".join(top_teams) if top_teams else "Tournament just starting"

        prompt = f"""Create a compelling daily briefing for World Cup Day {len(results) // 3 + 1}:

Tournament Status:
- {results_summary} completed
- Top performers so far: {top_performers}

Highlight the key storylines and what to watch for today.
Make it exciting and memorable!"""

        return self.chat(prompt, system=system_prompt, temperature=0.8, max_tokens=300)

    def suggest_injury_impact(
        self,
        team: str,
        injury_report: str,
        current_elo: float,
    ) -> LLMResult:
        """
        Analyze how an injury might affect team performance.

        Returns a suggested Elo adjustment factor.
        """
        system_prompt = """You are a sports medicine and tactics expert.
Assess how player injuries affect team strength.
Provide a numerical impact score from 0 (no impact) to -0.3 (major impact)."""

        prompt = f"""Analyze the impact of this injury on {team}:

Injury Report: {injury_report}
Current Team Strength (Elo): {current_elo}

What is the expected impact on their tournament performance?
Consider: position affected, player importance, squad depth.
Respond with a brief analysis and a suggested impact score (0 to -0.3)."""

        return self.chat(prompt, system=system_prompt, temperature=0.3, max_tokens=200)


# ── Async wrapper ────────────────────────────────────────────────────────────────

class AsyncLLMEngine(LLMEngine):
    """Async version of LLMEngine for high-performance usage."""

    async def chat_async(self, prompt: str, system: str | None = None, **kwargs) -> LLMResult:
        """Async chat completion."""
        import time
        import asyncio
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                latency_ms = (time.time() - start_time) * 1000

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                return LLMResult(
                    content=content,
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    latency_ms=latency_ms,
                    success=True,
                )

        except Exception as e:
            return LLMResult(
                content="",
                model=self.model,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def analyze_match_result_async(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        world_state_context: dict | None = None,
    ) -> LLMResult:
        """Async version of analyze_match_result."""
        result = self.analyze_match_result(
            home_team, away_team, home_score, away_score, world_state_context
        )
        # For sync API, just return the sync result
        # In production, this would call chat_async
        return result


# ── Fallback for demo/testing ──────────────────────────────────────────────────

class MockLLMEngine:
    """Mock LLM engine for testing without API access."""

    def analyze_match_result(self, home_team, away_team, home_score, away_score, context=None):
        winner = home_team if home_score > away_score else away_team if away_score > home_score else None
        if winner:
            return LLMResult(
                content=f"[MOCK] {winner} wins! This result {'boosts' if home_score > away_score else 'reduces'} their qualification chances.",
                model="mock",
                success=True,
            )
        return LLMResult(
            content=f"[MOCK] {home_team} and {away_team} split the points. Both teams need to win their remaining matches.",
            model="mock",
            success=True,
        )

    def generate_prediction_explanation(self, home, away, h_prob, d_prob, a_prob, factors=None):
        return LLMResult(
            content=f"[MOCK] Based on recent form and Elo ratings, {home} has a {h_prob:.0%} chance of winning.",
            model="mock",
            success=True,
        )

    def summarize_tournament_state(self, state):
        return LLMResult(
            content=f"[MOCK] Day {len(state.get('results', [])) // 3 + 1} of the World Cup! Exciting times ahead.",
            model="mock",
            success=True,
        )

    def suggest_injury_impact(self, team, report, elo):
        return LLMResult(
            content=f"[MOCK] The injury to {team} reduces their strength by approximately 5%.",
            model="mock",
            success=True,
        )


def create_llm_engine(use_mock: bool = False) -> LLMEngine | MockLLMEngine:
    """Factory function to create LLM engine with fallback."""
    if use_mock:
        return MockLLMEngine()

    try:
        return LLMEngine()
    except ValueError:
        print("Warning: LLM API key not found, using mock engine")
        return MockLLMEngine()
