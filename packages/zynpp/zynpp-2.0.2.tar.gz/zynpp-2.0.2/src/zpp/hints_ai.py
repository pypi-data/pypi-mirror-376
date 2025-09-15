from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from .utils import get_logger, getenv_bool

LOGGER = get_logger("hints_ai")


class Breaker:
    def __init__(self, max_fail: int = 3, cool_seconds: int = 300) -> None:
        self.fail = 0
        self.until = 0.0
        self.max_fail = max_fail
        self.cool_seconds = cool_seconds

    def allow(self, now: float) -> bool:
        return now >= self.until

    def record(self, ok: bool, now: float) -> None:
        if ok:
            self.fail = 0
            self.until = 0.0
        else:
            self.fail += 1
            if self.fail >= self.max_fail:
                self.until = now + float(self.cool_seconds)


_BREAKER = Breaker()


@dataclass
class AISuggestion:
    title: str
    rationale: str
    code_before_snippet: str
    code_after_snippet: str
    risk_notes: str
    estimated_speedup_pct: int


def _provider_from_env() -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    return None


def ai_enabled() -> bool:
    if getenv_bool("ZPP_SAFE_MODE", False):
        return False
    return _provider_from_env() is not None


def _prompt_for_code(snippet: str) -> str:
    return (
        "You are a C++ performance expert. Analyze the snippet and return JSON with key 'suggestions'\n"
        "Each suggestion has: title, rationale, code_before_snippet, code_after_snippet, risk_notes, estimated_speedup_pct (integer).\n"
        "Respond with ONLY JSON.\n\nSnippet:\n" + snippet
    )


async def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout_s: float) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        return await client.post(url, headers=headers, json=payload)


def select_hot_spans(code: str, max_lines: int = 300) -> str:
    lines = code.splitlines()
    return "\n".join(lines[:max_lines])


async def get_ai_hints(source_path: Path, timeout_s: float = 6.0) -> list[AISuggestion]:
    now = time.time()
    if not _BREAKER.allow(now):
        LOGGER.info("AI breaker open; skipping AI hints")
        return []
    provider = _provider_from_env()
    if provider is None:
        return []
    code = source_path.read_text(encoding="utf-8", errors="ignore")
    prompt = _prompt_for_code(select_hot_spans(code))

    try:
        if provider == "openai":
            key = os.environ["OPENAI_API_KEY"]
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a concise C++ performance assistant."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }
        elif provider == "gemini":
            key = os.environ["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2},
            }
        else:  # groq
            key = os.environ["GROQ_API_KEY"]
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a concise C++ performance assistant."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }

        resp = await _post_json(url, headers, payload, timeout_s)
        ok = resp.status_code == 200
        _BREAKER.record(ok, now=time.time())
        if not ok:
            LOGGER.info("AI HTTP %s: %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
        if provider == "gemini":
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            obj = json.loads(text)
        else:
            content = data["choices"][0]["message"]["content"]
            obj = json.loads(content)
        results: list[AISuggestion] = []
        for s in obj.get("suggestions", []):
            try:
                results.append(
                    AISuggestion(
                        title=s.get("title", ""),
                        rationale=s.get("rationale", ""),
                        code_before_snippet=s.get("code_before_snippet", ""),
                        code_after_snippet=s.get("code_after_snippet", ""),
                        risk_notes=s.get("risk_notes", ""),
                        estimated_speedup_pct=int(s.get("estimated_speedup_pct", 0)),
                    )
                )
            except Exception:
                continue
        return results
    except Exception as e:
        _BREAKER.record(False, now=time.time())
        LOGGER.info("AI error: %s", e)
        return []


