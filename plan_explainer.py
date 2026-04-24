"""AI-powered plan explainer with RAG-grounded knowledge.

Takes a generated plan and produces a human-readable rationale that
references pet profiles, owner preferences, scheduling constraints,
AND relevant pet-care knowledge retrieved from a local knowledge base.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai_client import AIClientError, GeminiClient
from knowledge_retriever import KnowledgeRetriever

if TYPE_CHECKING:
    from pawpal_system import Owner, Task

logger = logging.getLogger("pawpal.explainer")

# Singleton: load the knowledge base once per process.
_retriever: KnowledgeRetriever | None = None


def _get_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


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

## Relevant pet-care knowledge (use ONLY if it helps explain the plan)
{knowledge_block}

## Your job
Write a concise explanation (50-80 words) that:
1. Opens with a one-sentence summary of the plan.
2. Briefly notes WHY 1-2 key tasks are timed this way. If the knowledge
   above is relevant, weave in ONE specific fact from it naturally.
3. Ends with one short practical tip.

Rules:
- Use plain language, not bullet symbols like * or #.
- Do not invent tasks, times, pets, or facts not in the data above.
- If the knowledge snippets do not fit, ignore them — do not force them in.
- Do not mention that you are an AI or that you retrieved knowledge.
- Keep it under 90 words.
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


def _build_retrieval_query(owner: "Owner", plan: list["Task"]) -> str:
    """Construct a query string from plan + pet context for retrieval."""
    parts: list[str] = []
    for pet in owner.pets:
        parts.append(f"{pet.species} {pet.notes}")
    for task in plan:
        parts.append(f"{task.title} {task.category}")
    return " ".join(parts)


def _format_knowledge_block(snippets: list[dict]) -> str:
    if not snippets:
        return "(no relevant knowledge found)"
    lines = []
    for snippet in snippets:
        lines.append(f"- [{snippet['topic']}] {snippet['content']}")
    return "\n".join(lines)


def explain_plan_with_ai(
    plan: list["Task"],
    owner: "Owner",
    task_pet_map: dict[int, str],
    client: GeminiClient | None = None,
    retriever: KnowledgeRetriever | None = None,
) -> tuple[str, list[dict]]:
    """Produce a friendly AI explanation grounded in retrieved knowledge.

    Returns (explanation_text, retrieved_snippets) so the UI can show
    the user what knowledge was used.

    Raises AIClientError on failure — caller should fall back to the
    deterministic explain_plan() output.
    """
    if not plan:
        return "No plan generated yet.", []

    if client is None:
        client = GeminiClient()
    if retriever is None:
        retriever = _get_retriever()

    # Retrieve top-3 relevant knowledge snippets
    query = _build_retrieval_query(owner, plan)
    snippets = retriever.retrieve(query, top_k=3)

    preferences = ", ".join(owner.preferences) if owner.preferences else "none"

    prompt = EXPLAIN_PROMPT_TEMPLATE.format(
        owner_name=owner.name,
        available_time=owner.available_time,
        preferences=preferences,
        pets_block=_format_pets_block(owner),
        plan_block=_format_plan_block(plan, task_pet_map),
        knowledge_block=_format_knowledge_block(snippets),
    )

    logger.info(
        "Explaining plan: %d task(s), %d knowledge snippet(s)",
        len(plan), len(snippets),
    )
    text = client.generate_text(prompt, temperature=0.5)
    return text, snippets
