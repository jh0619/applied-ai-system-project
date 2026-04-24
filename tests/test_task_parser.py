"""Tests for task_parser (no live API calls)."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from task_parser import TaskParseError, parse_tasks_from_text


def _mock_client(return_value):
    client = MagicMock()
    client.generate_json.return_value = return_value
    return client


def test_parse_single_task_with_relative_time():
    fake = _mock_client([{
        "title": "Morning walk",
        "duration": 30,
        "priority": "high",
        "category": "exercise",
        "time": "2026-04-25 08:00 AM",
        "frequency": "",
        "description": "Walk with Mochi",
        "pet_name": "Mochi",
    }])
    tasks = parse_tasks_from_text(
        "Walk Mochi tomorrow at 8am for 30 min, high priority",
        pet_names=["Mochi"],
        client=fake,
        today=date(2026, 4, 24),
    )
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Morning walk"
    assert tasks[0]["priority"] == "high"
    assert tasks[0]["pet_name"] == "Mochi"


def test_parse_multiple_tasks():
    fake = _mock_client([
        {"title": "Walk", "duration": 30, "priority": "high",
         "category": "exercise", "time": "", "frequency": "",
         "description": "", "pet_name": "Mochi"},
        {"title": "Feed", "duration": 10, "priority": "high",
         "category": "feeding", "time": "", "frequency": "daily",
         "description": "", "pet_name": "Mochi"},
    ])
    tasks = parse_tasks_from_text("Walk and feed Mochi", ["Mochi"], client=fake)
    assert len(tasks) == 2
    assert {t["title"] for t in tasks} == {"Walk", "Feed"}


def test_invalid_priority_falls_back_to_medium():
    fake = _mock_client([{
        "title": "Play", "duration": 15, "priority": "urgent",
        "category": "enrichment", "time": "", "frequency": "",
        "description": "", "pet_name": "",
    }])
    tasks = parse_tasks_from_text("Play with pet", [], client=fake)
    assert tasks[0]["priority"] == "medium"


def test_pet_name_case_insensitive_match():
    fake = _mock_client([{
        "title": "Brush", "duration": 10, "priority": "low",
        "category": "grooming", "time": "", "frequency": "",
        "description": "", "pet_name": "mochi",
    }])
    tasks = parse_tasks_from_text("Brush mochi", ["Mochi"], client=fake)
    assert tasks[0]["pet_name"] == "Mochi"


def test_pet_name_unknown_becomes_empty():
    fake = _mock_client([{
        "title": "Walk", "duration": 20, "priority": "high",
        "category": "exercise", "time": "", "frequency": "",
        "description": "", "pet_name": "Rex",
    }])
    tasks = parse_tasks_from_text("Walk Rex", ["Mochi"], client=fake)
    assert tasks[0]["pet_name"] == ""


def test_empty_input_raises():
    with pytest.raises(TaskParseError):
        parse_tasks_from_text("   ", ["Mochi"], client=_mock_client([]))


def test_empty_ai_result_raises():
    with pytest.raises(TaskParseError):
        parse_tasks_from_text("Walk dog", ["Mochi"], client=_mock_client([]))


def test_single_dict_response_is_wrapped():
    fake = _mock_client({
        "title": "Walk", "duration": 20, "priority": "high",
        "category": "exercise", "time": "", "frequency": "",
        "description": "", "pet_name": "Mochi",
    })
    tasks = parse_tasks_from_text("Walk Mochi", ["Mochi"], client=fake)
    assert len(tasks) == 1
