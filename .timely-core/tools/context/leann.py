"""Timely-native lightweight retrieval index fed from CXDB documents."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .cxdb import ContextDocument


SCHEMA_VERSION = 1
DIMENSIONS = 192
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _tokenize(text: str) -> List[str]:
    lowered = text.lower()
    tokens = TOKEN_RE.findall(lowered)
    features = list(tokens)
    for token in tokens:
        if len(token) < 4:
            continue
        for idx in range(len(token) - 2):
            features.append(f"tri:{token[idx:idx + 3]}")
    return features


def _vectorize(text: str) -> List[float]:
    features = _tokenize(text)
    if not features:
        return [0.0] * DIMENSIONS

    vector = [0.0] * DIMENSIONS
    for feature in features:
        slot = int(hashlib.sha1(feature.encode("utf-8")).hexdigest(), 16) % DIMENSIONS
        vector[slot] += 1.0

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _dot(left: List[float], right: List[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _snippet(text: str, query: str, limit: int = 180) -> str:
    if not text:
        return ""
    lowered = text.lower()
    query_tokens = [token for token in TOKEN_RE.findall(query.lower()) if token]
    if not query_tokens:
        return text[:limit].strip()

    positions = [lowered.find(token) for token in query_tokens if lowered.find(token) >= 0]
    if not positions:
        return text[:limit].strip()

    start = max(0, min(positions) - 40)
    end = min(len(text), start + limit)
    return text[start:end].strip()


class LEANNIndex:
    """Persist and query a local retrieval index for CXDB documents."""

    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path

    def build(self, documents: Iterable[ContextDocument]) -> Dict[str, Any]:
        docs = list(documents)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "dimensions": DIMENSIONS,
            "documents": [
                {
                    "id": doc.doc_id,
                    "kind": doc.kind,
                    "title": doc.title,
                    "body": doc.body,
                    "source_path": doc.source_path,
                    "metadata": doc.metadata or {},
                    "vector": _vectorize(" ".join([doc.title, doc.body, doc.source_path or ""])),
                }
                for doc in docs
            ],
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {
            "documents": len(docs),
            "index_path": str(self.index_path),
            "generated_at": payload["generated_at"],
        }

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.index_path.exists():
            return []
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        query_vector = _vectorize(query)
        results: List[Dict[str, Any]] = []
        for doc in payload.get("documents", []):
            score = _dot(query_vector, doc.get("vector", []))
            if score <= 0:
                continue
            results.append(
                {
                    "id": doc["id"],
                    "kind": doc["kind"],
                    "title": doc["title"],
                    "source_path": doc.get("source_path"),
                    "metadata": doc.get("metadata", {}),
                    "score": round(score, 4),
                    "snippet": _snippet(doc.get("body", ""), query),
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[: max(1, limit)]
