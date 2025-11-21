import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np

from . import embedder
from . import cache_manager


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SearchResult:
    doc_id: str
    score: float
    cosine_sim: float
    overlap_ratio: float
    len_score: float
    overlap_keywords: List[str]
    preview: str
    category: str
    reason: str


class SearchEngine:
    def __init__(self, index: faiss.IndexFlatIP, id_mapping: List[str]):
        self.index = index
        self.id_mapping = id_mapping

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9]+", text.lower())

    @staticmethod
    def _make_preview(text: str, max_chars: int = 400) -> str:
        text = text.strip().replace("\n", " ")
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    def _compute_explanation(
        self,
        query: str,
        doc_text: str,
        doc_length_tokens: int,
        cosine_sim: float,
    ) -> Dict[str, Any]:
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(doc_text)
        q_set = set(q_tokens)
        d_set = set(d_tokens)
        overlap = sorted(q_set & d_set)
        overlap_ratio = (len(overlap) / len(q_set)) if q_set else 0.0

        # Prefer shorter documents slightly, but keep score in [0, 1]
        len_score = 1.0 / (1.0 + math.log(1.0 + max(doc_length_tokens, 1)))

        final_score = 0.7 * float(cosine_sim) + 0.2 * overlap_ratio + 0.1 * len_score

        if overlap:
            reason = f"Semantic match with overlapping keywords: {', '.join(overlap[:5])}."
        else:
            reason = "High semantic similarity even without exact keyword overlap."

        return {
            "score": float(final_score),
            "cosine_sim": float(cosine_sim),
            "overlap_ratio": float(overlap_ratio),
            "len_score": float(len_score),
            "overlap_keywords": overlap,
            "reason": reason,
        }

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not query.strip():
            return []

        q_emb = embedder.embed_query(query)
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q_emb, k)
        scores_row = scores[0]
        indices_row = indices[0]

        results: List[SearchResult] = []
        for score, idx in zip(scores_row, indices_row):
            if idx < 0 or idx >= len(self.id_mapping):
                continue
            doc_id = self.id_mapping[idx]
            doc = cache_manager.get_document(doc_id)
            if not doc:
                continue

            # Read document text from disk
            try:
                text = Path(doc.filepath).read_text(encoding="utf-8", errors="ignore")
            except FileNotFoundError:
                text = ""

            explanation = self._compute_explanation(
                query=query,
                doc_text=text,
                doc_length_tokens=doc.length_tokens,
                cosine_sim=float(score),
            )

            preview = self._make_preview(text)
            results.append(
                SearchResult(
                    doc_id=doc.doc_id,
                    score=explanation["score"],
                    cosine_sim=explanation["cosine_sim"],
                    overlap_ratio=explanation["overlap_ratio"],
                    len_score=explanation["len_score"],
                    overlap_keywords=explanation["overlap_keywords"],
                    preview=preview,
                    category=doc.category,
                    reason=explanation["reason"],
                )
            )

        # Sort again by our composite score, just in case
        results.sort(key=lambda r: r.score, reverse=True)
        return results


def results_to_dict(results: List[SearchResult]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in results]


