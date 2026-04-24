"""AI-powered plan explainer.

Takes a generated plan and produces a human-readable rationale that
references pet profiles, owner preferences, and scheduling constraints.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai_client import AIClientError, GeminiClient

if TYPE_CHECKING:
    from pawpal_system import Owner, Task

logger = logging.getLogger("pawpal.explainer")


EXPLAIN_PROMPT_TEMPLATE = """You are PawPal+, a warm and practical pet-care planning assistant.

Explain the daily plan below to the owner in a friendly, conversational tone.

## Owner
- Name: {owner_name}
- Available time today: {available_time} minutes
- Preferences: {preferences}

## Pets
{pets_block}

## Today's generated plan (already sorted by priority)
{plan_block}

## Your job
Write a short explanation (90-120 words) that:
1. Opens with a one-sentence summary of the plan.
2. Groups tasks by pet and briefly explains WHY each task is scheduled
   when it is — reference the pet's profile, the priority level, or the
   owner's preferences when relevant.
3. Ends with one practical tip for the day.

Rules:
- Use plain language, not bullet symbols like * or #.
- Do not invent tasks, times, or pets that are not in the data above.
- Do not mention that you are an AI.
- Keep it under 120 words.
"""


def _format_pets_block(owner: "Owner") -> str:
    if not owner.pets:
        return "(no pets)"
    lines = []
    for pet in owner.pets:
        lines.append(
            f"- {pet.name} ({pet.species}, age {pet.age}): "
            f"{pet.notes or 'no notes'}"
        )
    return "\n".join(lines)


def _format_plan_block(
    plan: list["Task"],
    task_pet_map: dict[int, str],
) -> str:
    if not plan:
        return "(empty plan)"
    lines = []
    for idx, task in enumerate(plan, 1):
        pet_name = task_pet_map.get(id(task), "Unknown pet")
        time_label = task.time or "no time set"
        lines.append(
            f"{idx}. {task.title} — pet: {pet_name}, "
            f"time: {time_label}, duration: {task.duration} min, "
            f"priority: {task.priority}, category: {task.category}"
        )
    return "\n".join(lines)


def explain_plan_with_ai(
    plan: list["Task"],
    owner: "Owner",
    task_pet_map: dict[int, str],
    client: GeminiClient | None = None,
) -> str:
    """Produce a friendly AI-generated explanation of the plan.

    Raises AIClientError on failure — caller should fall back to the
    deterministic explain_plan() output.
    """
    if not plan:
        return "No plan generated yet."

    if client is None:
        client = GeminiClient()

    preferences = ", ".join(owner.preferences) if owner.preferences else "none"

    prompt = EXPLAIN_PROMPT_TEMPLATE.format(
        owner_name=owner.name,
        available_time=owner.available_time,
        preferences=preferences,
        pets_block=_format_pets_block(owner),
        plan_block=_format_plan_block(plan, task_pet_map),
    )

    logger.info("Explaining plan with %d task(s)", len(plan))
    return client.generate_text(prompt, temperature=0.5)
