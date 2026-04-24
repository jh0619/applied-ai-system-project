"""Tests for plan_explainer (no live API calls)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pawpal_system import Owner, Pet, Task
from plan_explainer import explain_plan_with_ai
from ai_client import AIClientError


def _build_owner_with_plan():
    owner = Owner("Jordan", 120, ["morning routine"])
    mochi = Pet("Mochi", "dog", 2, "Energetic golden retriever")
    owner.add_pet(mochi)
    walk = Task("Morning walk", 30, "high", "exercise", time="8:00 AM")
    feed = Task("Feed Mochi", 10, "high", "feeding", time="8:30 AM")
    mochi.tasks.extend([walk, feed])
    return owner, [walk, feed]


def _fake_retriever(snippets=None):
    """Return a mock retriever that yields the given snippets."""
    retriever = MagicMock()
    retriever.retrieve.return_value = snippets or []
    return retriever


def test_returns_ai_text_when_plan_exists():
    owner, plan = _build_owner_with_plan()
    fake_client = MagicMock()
    fake_client.generate_text.return_value = (
        "Here's a calm morning for Mochi: a 30-min walk at 8am..."
    )

    text, snippets = explain_plan_with_ai(
        plan=plan,
        owner=owner,
        task_pet_map=owner.get_task_pet_map(),
        client=fake_client,
        retriever=_fake_retriever(),
    )

    assert "Mochi" in text
    assert isinstance(snippets, list)
    fake_client.generate_text.assert_called_once()


def test_empty_plan_returns_default_message():
    owner = Owner("Jordan", 120, [])
    fake_client = MagicMock()

    text, snippets = explain_plan_with_ai(
        plan=[],
        owner=owner,
        task_pet_map={},
        client=fake_client,
        retriever=_fake_retriever(),
    )

    assert "No plan" in text
    assert snippets == []
    fake_client.generate_text.assert_not_called()


def test_prompt_includes_pet_and_task_context():
    owner, plan = _build_owner_with_plan()
    fake_client = MagicMock()
    fake_client.generate_text.return_value = "ok"

    explain_plan_with_ai(
        plan=plan,
        owner=owner,
        task_pet_map=owner.get_task_pet_map(),
        client=fake_client,
        retriever=_fake_retriever(),
    )

    prompt_sent = fake_client.generate_text.call_args[0][0]
    assert "Mochi" in prompt_sent
    assert "Morning walk" in prompt_sent
    assert "Jordan" in prompt_sent
    assert "morning routine" in prompt_sent
    # RAG: prompt should include the knowledge block heading
    assert "pet-care knowledge" in prompt_sent.lower()


def test_ai_error_propagates_for_ui_fallback():
    owner, plan = _build_owner_with_plan()
    fake_client = MagicMock()
    fake_client.generate_text.side_effect = AIClientError("network down")

    with pytest.raises(AIClientError):
        explain_plan_with_ai(
            plan=plan,
            owner=owner,
            task_pet_map=owner.get_task_pet_map(),
            client=fake_client,
            retriever=_fake_retriever(),
        )


def test_retrieved_snippets_are_returned_to_caller():
    """RAG: the retriever's snippets should flow back to the UI."""
    owner, plan = _build_owner_with_plan()
    fake_client = MagicMock()
    fake_client.generate_text.return_value = "ok"
    snippets_in = [
        {"topic": "dog exercise", "content": "Dogs need exercise.", "score": 0.42},
    ]

    _, snippets_out = explain_plan_with_ai(
        plan=plan,
        owner=owner,
        task_pet_map=owner.get_task_pet_map(),
        client=fake_client,
        retriever=_fake_retriever(snippets_in),
    )

    assert snippets_out == snippets_in


def test_knowledge_block_included_in_prompt_when_snippets_exist():
    owner, plan = _build_owner_with_plan()
    fake_client = MagicMock()
    fake_client.generate_text.return_value = "ok"
    snippets_in = [
        {"topic": "dog exercise",
         "content": "Dogs need 30-120 minutes of exercise daily.",
         "score": 0.42},
    ]

    explain_plan_with_ai(
        plan=plan,
        owner=owner,
        task_pet_map=owner.get_task_pet_map(),
        client=fake_client,
        retriever=_fake_retriever(snippets_in),
    )

    prompt_sent = fake_client.generate_text.call_args[0][0]
    assert "Dogs need 30-120 minutes" in prompt_sent
    assert "dog exercise" in prompt_sent
