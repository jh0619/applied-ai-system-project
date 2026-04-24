"""Simple TF-IDF based retrieval over the pet-care knowledge base.

Kept intentionally dependency-light: TF-IDF scoring is implemented by
hand using Python's Counter, so the project stays portable.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("pawpal.rag")

_DEFAULT_PATH = Path(__file__).parent / "data" / "knowledge_base.json"
_TOKEN_RE = re.compile(r"[a-zA-Z]+")

# Common English words we don't want to match on.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at",
    "for", "with", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "but", "if", "then",
    "than", "that", "this", "these", "those", "it", "its", "as",
    "from", "by", "about", "your", "you", "my", "their", "he", "she",
    "they", "we", "i", "me", "him", "her", "us", "them", "some",
    "any", "all", "each", "every", "no", "not",
}


def _tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


class KnowledgeRetriever:
    """Loads the knowledge base once and retrieves top-k relevant snippets."""

    def __init__(self, kb_path: Path | str = _DEFAULT_PATH):
        self.kb_path = Path(kb_path)
        self.entries: list[dict[str, Any]] = []
        self._tokenized: list[Counter] = []
        self._idf: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self.kb_path.exists():
            logger.warning("Knowledge base file not found: %s", self.kb_path)
            return
        with self.kb_path.open("r", encoding="utf-8") as fp:
            self.entries = json.load(fp)

        self._tokenized = [
            Counter(_tokenize(f"{e['topic']} {e['content']}"))
            for e in self.entries
        ]

        # Compute IDF for each unique term
        num_docs = len(self._tokenized)
        doc_freq: Counter = Counter()
        for tokens in self._tokenized:
            for term in tokens:
                doc_freq[term] += 1
        self._idf = {
            term: math.log((num_docs + 1) / (freq + 1)) + 1
            for term, freq in doc_freq.items()
        }
        logger.info(
            "Loaded knowledge base: %d entries, %d unique terms",
            len(self.entries), len(self._idf),
        )

    def _score(self, query_tokens: list[str], doc_tokens: Counter) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        score = 0.0
        doc_len = sum(doc_tokens.values())
        for term in query_tokens:
            if term in doc_tokens:
                tf = doc_tokens[term] / doc_len
                idf = self._idf.get(term, 0.0)
                score += tf * idf
        return score

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return the top-k most relevant knowledge entries for a query.

        Each result is a dict with topic, content, and a score. Returns
        an empty list if no entries match.
        """
        if not self.entries:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, dict[str, Any]]] = []
        for entry, tokens in zip(self.entries, self._tokenized):
            score = self._score(query_tokens, tokens)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:top_k]:
            results.append({
                "topic": entry["topic"],
                "content": entry["content"],
                "score": round(score, 4),
            })
        logger.info(
            "Retrieved %d/%d entries for query (len=%d)",
            len(results), len(self.entries), len(query),
        )
        return results
