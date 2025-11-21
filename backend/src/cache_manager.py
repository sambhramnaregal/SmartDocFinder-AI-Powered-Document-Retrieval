import io
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cache.db"


@dataclass
class Document:
    doc_id: str
    filepath: str
    category: str
    length_tokens: int
    sha256_hash: str


def _get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite schema for documents and embeddings."""

    conn = _get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            category TEXT,
            length_tokens INTEGER NOT NULL,
            sha256_hash TEXT NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            doc_id TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()


def upsert_document(doc: Document) -> None:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents (doc_id, filepath, category, length_tokens, sha256_hash)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
            filepath = excluded.filepath,
            category = excluded.category,
            length_tokens = excluded.length_tokens,
            sha256_hash = excluded.sha256_hash;
        """,
        (doc.doc_id, doc.filepath, doc.category, doc.length_tokens, doc.sha256_hash),
    )
    conn.commit()
    conn.close()


def get_document(doc_id: str) -> Optional[Document]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return Document(
        doc_id=row["doc_id"],
        filepath=row["filepath"],
        category=row["category"] or "",
        length_tokens=row["length_tokens"],
        sha256_hash=row["sha256_hash"],
    )


def iter_documents() -> Iterable[Document]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        yield Document(
            doc_id=row["doc_id"],
            filepath=row["filepath"],
            category=row["category"] or "",
            length_tokens=row["length_tokens"],
            sha256_hash=row["sha256_hash"],
        )


def _embedding_to_blob(embedding: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, embedding.astype("float32"))
    return buf.getvalue()


def _blob_to_embedding(blob: bytes) -> np.ndarray:
    buf = io.BytesIO(blob)
    return np.load(buf).astype("float32")


def upsert_embedding(doc_id: str, embedding: np.ndarray) -> None:
    conn = _get_connection()
    cur = conn.cursor()
    blob = _embedding_to_blob(embedding)
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        INSERT INTO embeddings (doc_id, embedding, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
            embedding = excluded.embedding,
            updated_at = excluded.updated_at;
        """,
        (doc_id, blob, now),
    )
    conn.commit()
    conn.close()


def get_all_embeddings_and_ids() -> Tuple[List[str], np.ndarray]:
    """Return all (doc_id, embedding) pairs for index building."""

    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT doc_id, embedding FROM embeddings")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return [], np.zeros((0, 0), dtype="float32")

    ids: List[str] = []
    embs: List[np.ndarray] = []
    for row in rows:
        ids.append(row["doc_id"])
        embs.append(_blob_to_embedding(row["embedding"]))
    emb_matrix = np.vstack(embs).astype("float32")
    return ids, emb_matrix


def get_stats() -> Dict[str, int]:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM documents")
    docs_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM embeddings")
    emb_count = cur.fetchone()["c"]
    conn.close()
    return {"documents": docs_count, "embeddings": emb_count}


