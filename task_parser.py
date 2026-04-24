"""Natural-language task parser powered by Gemini.

Takes free-form user text and returns structured task dicts compatible
with the Task dataclass.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from ai_client import AIClientError, GeminiClient

logger = logging.getLogger("pawpal.parser")

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_FREQUENCIES = {"", "daily", "weekly"}


PARSE_PROMPT_TEMPLATE = """You are a pet-care task parser for an app called PawPal+.

Today's date is {today}.
The available pets are: {pet_names}.

Convert the user's natural-language request into a JSON array of task
objects. Each task object MUST have these exact keys:
- "title" (string, short action name, e.g. "Morning walk")
- "duration" (integer, minutes; estimate if not specified)
- "priority" (string, one of: "low", "medium", "high")
- "category" (string, one of: "feeding", "exercise", "grooming", "health", "enrichment", "other")
- "time" (string, format "YYYY-MM-DD HH:MM AM/PM", or empty string if not specified)
- "frequency" (string, one of: "", "daily", "weekly")
- "description" (string, one short sentence; may be empty)
- "pet_name" (string, must match one of the available pets exactly, or empty if ambiguous)

Rules:
- Resolve relative time ("tomorrow", "tonight", "in an hour") using today's date.
- If the user mentions multiple tasks, return multiple objects.
- If duration is not mentioned, estimate a reasonable default for the activity.
- If priority is not mentioned, default to "medium".
- Return ONLY the JSON array, no markdown, no explanation.

User request:
\"\"\"{user_text}\"\"\"
"""


class TaskParseError(Exception):
    """Raised when user input cannot be parsed into tasks."""


def _coerce_task_dict(raw: dict[str, Any], pet_names: list[str]) -> dict[str, Any]:
    """Validate and normalize a single task dict from the LLM."""
    title = str(raw.get("title", "")).strip()
    if not title:
        raise TaskParseError("Task is missing a title.")

    try:
        duration = int(raw.get("duration", 15))
    except (TypeError, ValueError):
        duration = 15
    duration = max(1, min(duration, 240))

    priority = str(raw.get("priority", "medium")).strip().lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"

    category = str(raw.get("category", "other")).strip().lower() or "other"
    time_value = str(raw.get("time", "")).strip()
    frequency = str(raw.get("frequency", "")).strip().lower()
    if frequency not in VALID_FREQUENCIES:
        frequency = ""

    description = str(raw.get("description", "")).strip()

    pet_name = str(raw.get("pet_name", "")).strip()
    # Match pet name case-insensitively
    if pet_name:
        match = next(
            (p for p in pet_names if p.lower() == pet_name.lower()),
            "",
        )
        pet_name = match

    return {
        "title": title,
        "duration": duration,
        "priority": priority,
        "category": category,
        "time": time_value,
        "frequency": frequency,
        "description": description,
        "pet_name": pet_name,
    }


def parse_tasks_from_text(
    user_text: str,
    pet_names: list[str],
    client: GeminiClient | None = None,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """Parse free-form pet-care request into a list of task dicts.

    Raises TaskParseError on any failure. Caller is responsible for
    catching and surfacing a friendly message.
    """
    user_text = (user_text or "").strip()
    if not user_text:
        raise TaskParseError("Please describe at least one task.")

    if client is None:
        try:
            client = GeminiClient()
        except AIClientError as exc:
            raise TaskParseError(str(exc)) from exc

    today = today or date.today()
    prompt = PARSE_PROMPT_TEMPLATE.format(
        today=today.isoformat(),
        pet_names=", ".join(pet_names) if pet_names else "(none)",
        user_text=user_text,
    )

    try:
        raw = client.generate_json(prompt)
    except AIClientError as exc:
        raise TaskParseError(f"AI parsing failed: {exc}") from exc

    # Gemini may return a dict with a single task, or a list. Normalize.
    if isinstance(raw, dict):
        raw_list = [raw]
    elif isinstance(raw, list):
        raw_list = raw
    else:
        raise TaskParseError("AI returned an unexpected response shape.")

    if not raw_list:
        raise TaskParseError("AI did not identify any tasks in your request.")

    parsed_tasks: list[dict[str, Any]] = []
    errors: list[str] = []
    for idx, item in enumerate(raw_list):
        if not isinstance(item, dict):
            errors.append(f"Task #{idx + 1} was not an object.")
            continue
        try:
            parsed_tasks.append(_coerce_task_dict(item, pet_names))
        except TaskParseError as exc:
            errors.append(f"Task #{idx + 1}: {exc}")

    if not parsed_tasks:
        raise TaskParseError(
            "Could not extract valid tasks. " + " ".join(errors)
        )

    logger.info(
        "Parsed %d task(s) from user input (len=%d)",
        len(parsed_tasks), len(user_text),
    )
    return parsed_tasks
