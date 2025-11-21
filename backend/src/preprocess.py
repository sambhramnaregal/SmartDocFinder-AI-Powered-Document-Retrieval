import argparse
import hashlib
import re
from pathlib import Path
from typing import List, Tuple

from . import cache_manager
from .cache_manager import Document
from . import embedder
from . import index_manager


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_DIR = PROJECT_ROOT / "data" / "docs"


def clean_text(raw: str) -> str:
    """Lowercase, strip HTML tags, and normalize whitespace."""

    text = raw.lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_documents(docs_dir: Path, max_docs: int = 0) -> List[Tuple[Document, str]]:
    """Walk docs_dir and return list of (Document, cleaned_text).

    If max_docs > 0, stop after collecting that many documents (useful for testing).
    """

    docs: List[Tuple[Document, str]] = []
    for path in docs_dir.rglob("*.txt"):
        rel_path = path.relative_to(docs_dir)
        doc_id = rel_path.as_posix()
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "default"

        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(raw_text)
        length_tokens = len(cleaned.split())
        sha = compute_hash(cleaned)

        doc = Document(
            doc_id=doc_id,
            filepath=str(path.resolve()),
            category=category,
            length_tokens=length_tokens,
            sha256_hash=sha,
        )
        docs.append((doc, cleaned))
        if max_docs > 0 and len(docs) >= max_docs:
            break
    return docs


def main(docs_dir: Path) -> None:
    print(f"Using docs directory: {docs_dir}")
    cache_manager.init_db()

    all_docs = scan_documents(docs_dir)
    print(f"Found {len(all_docs)} .txt documents")

    # Decide which documents need fresh embeddings
    to_embed_texts: List[str] = []
    to_embed_ids: List[str] = []

    for doc, cleaned_text in all_docs:
        existing = cache_manager.get_document(doc.doc_id)
        if existing is None or existing.sha256_hash != doc.sha256_hash:
            cache_manager.upsert_document(doc)
            to_embed_ids.append(doc.doc_id)
            to_embed_texts.append(cleaned_text)
        else:
            # Ensure metadata is up to date even if embedding is reused
            cache_manager.upsert_document(doc)

    print(f"Documents needing new embeddings: {len(to_embed_ids)}")

    if to_embed_ids:
        embeddings = embedder.embed_documents(to_embed_texts)
        for doc_id, emb in zip(to_embed_ids, embeddings):
            cache_manager.upsert_embedding(doc_id, emb)

    # Build FAISS index from all cached embeddings
    ids, emb_matrix = cache_manager.get_all_embeddings_and_ids()
    if not ids:
        print("No embeddings in cache; index not built.")
        return

    print(f"Building index over {len(ids)} documents...")
    index_manager.build_index(emb_matrix, ids)
    print("Index built and saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess docs and build index")
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=str(DEFAULT_DOCS_DIR),
        help="Directory containing .txt documents (default: data/docs)",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=0,
        help="If >0, limit processing to the first N documents (useful for testing)",
    )
    args = parser.parse_args()
    docs_dir = Path(args.docs_dir).resolve()
    docs_dir.mkdir(parents=True, exist_ok=True)
    max_docs = int(args.max_docs)

    if max_docs > 0:
        # Respect the limit by scanning only up to max_docs
        all_docs = scan_documents(docs_dir, max_docs=max_docs)
        if len(all_docs) > max_docs:
            print(f"Limiting processing to first {max_docs} documents (from {len(all_docs)})")
            # Implement a quick wrapper that runs the core logic on the sliced list
            from typing import List, Tuple

            def main_with_limit(docs_dir: Path, docs_slice: List[Tuple[cache_manager.Document, str]]) -> None:
                cache_manager.init_db()

                all_docs_loc = docs_slice

                print(f"Found {len(all_docs_loc)} .txt documents (limited)")

                # Decide which documents need fresh embeddings
                to_embed_texts: List[str] = []
                to_embed_ids: List[str] = []

                for doc, cleaned_text in all_docs_loc:
                    existing = cache_manager.get_document(doc.doc_id)
                    if existing is None or existing.sha256_hash != doc.sha256_hash:
                        cache_manager.upsert_document(doc)
                        to_embed_ids.append(doc.doc_id)
                        to_embed_texts.append(cleaned_text)
                    else:
                        cache_manager.upsert_document(doc)

                print(f"Documents needing new embeddings: {len(to_embed_ids)}")

                if to_embed_ids:
                    embeddings = embedder.embed_documents(to_embed_texts)
                    for doc_id, emb in zip(to_embed_ids, embeddings):
                        cache_manager.upsert_embedding(doc_id, emb)

                # Build FAISS index from all cached embeddings
                ids, emb_matrix = cache_manager.get_all_embeddings_and_ids()
                if not ids:
                    print("No embeddings in cache; index not built.")
                    return

                print(f"Building index over {len(ids)} documents...")
                index_manager.build_index(emb_matrix, ids)
                print("Index built and saved.")

            main_with_limit(docs_dir, all_docs[:max_docs])
        else:
            main(docs_dir)
    else:
        main(docs_dir)


