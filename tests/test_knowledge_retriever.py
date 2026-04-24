"""Tests for the knowledge retriever."""
from __future__ import annotations

import json

import pytest

from knowledge_retriever import KnowledgeRetriever, _tokenize


@pytest.fixture
def tmp_kb(tmp_path):
    kb = [
        {"id": "1", "topic": "dog exercise",
         "content": "Dogs need daily exercise to stay healthy."},
        {"id": "2", "topic": "cat grooming",
         "content": "Long-haired cats need regular brushing."},
        {"id": "3", "topic": "puppy feeding",
         "content": "Puppies need three to four small meals per day."},
    ]
    path = tmp_path / "kb.json"
    path.write_text(json.dumps(kb))
    return path


def test_tokenize_removes_stopwords_and_short_words():
    tokens = _tokenize("The dog needs to run")
    assert "the" not in tokens
    assert "to" not in tokens
    assert "dog" in tokens
    assert "needs" in tokens


def test_retrieve_returns_relevant_entry(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    results = r.retrieve("my dog needs exercise", top_k=1)
    assert len(results) == 1
    assert results[0]["topic"] == "dog exercise"


def test_retrieve_ranks_relevance_correctly(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    results = r.retrieve("cat brushing", top_k=3)
    assert results[0]["topic"] == "cat grooming"


def test_retrieve_returns_empty_on_no_match(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    results = r.retrieve("unicorn horoscope cryptocurrency", top_k=3)
    assert results == []


def test_retrieve_respects_top_k(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    results = r.retrieve("pet care health feeding exercise", top_k=2)
    assert len(results) <= 2


def test_missing_kb_file_does_not_crash(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    r = KnowledgeRetriever(missing)
    assert r.retrieve("anything") == []


def test_empty_query_returns_empty(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    assert r.retrieve("") == []
    assert r.retrieve("   ") == []


def test_scores_are_included_and_sorted(tmp_kb):
    r = KnowledgeRetriever(tmp_kb)
    results = r.retrieve("dog cat puppy exercise", top_k=3)
    scores = [res["score"] for res in results]
    assert scores == sorted(scores, reverse=True)
    assert all(s > 0 for s in scores)
