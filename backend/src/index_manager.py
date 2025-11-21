import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
INDEX_PATH = DATA_DIR / "index.faiss"
META_PATH = DATA_DIR / "index_meta.json"


def build_index(embeddings: np.ndarray, ids: List[str]) -> None:
    """Build and persist a FAISS inner-product index for the given embeddings."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if embeddings.size == 0:
        raise ValueError("No embeddings available to build index.")

    n, dim = embeddings.shape
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps({"ids": ids}, indent=2), encoding="utf-8")


def load_index() -> Tuple[faiss.IndexFlatIP, List[str]]:
    """Load FAISS index and id mapping; raises FileNotFoundError if missing."""

    if not INDEX_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError("Index files not found. Run preprocessing/index build first.")

    index = faiss.read_index(str(INDEX_PATH))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    ids: List[str] = list(meta.get("ids", []))
    return index, ids


