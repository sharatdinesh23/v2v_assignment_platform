"""AI grading via OpenRouter.

Sends the question, the expected input/output, and the student's code to an
OpenRouter chat model and asks for a provisional grade + short feedback.

The grade returned here is ALWAYS provisional: the caller stores it with
status ``ai_graded`` and an admin must accept or redo it before it becomes
final. The interface is deliberately small so a different provider can be
swapped in later by changing only this file.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import httpx

from .config import settings

_SYSTEM_PROMPT = (
    "You are a strict but fair programming teaching assistant. You grade a "
    "student's code submission against a problem statement and expected "
    "input/output. Respond ONLY with a compact JSON object of the form "
    '{"grade": <integer 0-100>, "feedback": "<two or three sentences>"}. '
    "Base the grade on correctness first, then clarity. Do not execute code; "
    "reason about it. Never include anything outside the JSON object."
)


@dataclass
class GradeResult:
    grade: str            # e.g. "87" (percentage) or "" on failure
    feedback: str
    ok: bool


def _build_user_prompt(
    question: str,
    expected_input: str,
    expected_output: str,
    code: str,
) -> str:
    return (
        f"PROBLEM:\n{question}\n\n"
        f"EXPECTED INPUT:\n{expected_input or '(none provided)'}\n\n"
        f"EXPECTED OUTPUT:\n{expected_output or '(none provided)'}\n\n"
        f"STUDENT SUBMISSION:\n```\n{code}\n```\n\n"
        "Grade this submission now."
    )


def _extract_json(text: str) -> dict:
    """Best-effort parse of a JSON object out of a model reply."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


def grade_submission(
    question: str,
    expected_input: str,
    expected_output: str,
    code: str,
) -> GradeResult:
    """Call OpenRouter and return a provisional grade.

    Falls back to a clear, non-crashing result if OpenRouter is not configured
    or the request fails, so the submission still lands in the review queue.
    """
    if not settings.openrouter_configured:
        return GradeResult(
            grade="",
            feedback="AI grading skipped: OPENROUTER_API_KEY is not configured.",
            ok=False,
        )
    if not (code or "").strip():
        return GradeResult(grade="0", feedback="Empty submission.", ok=True)

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    question, expected_input, expected_output, code
                ),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        # OpenRouter recommends these for attribution; harmless if unused.
        "HTTP-Referer": "http://localhost",
        "X-Title": "Code Arena",
    }
    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        return GradeResult(
            grade="",
            feedback=f"AI grading failed: {exc}",
            ok=False,
        )

    parsed = _extract_json(content)
    grade = parsed.get("grade", "")
    feedback = parsed.get("feedback", content[:500])
    if grade == "" and not feedback:
        return GradeResult(grade="", feedback="AI returned no grade.", ok=False)
    return GradeResult(grade=str(grade), feedback=str(feedback), ok=True)
