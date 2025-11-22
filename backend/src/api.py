from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import cache_manager
from . import index_manager
from .search_engine import SearchEngine, results_to_dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="SmartDocFinder – AI-Powered Document Retrieval API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
             "https://smartdocfinder-ai-powered-document-2ls4.onrender.com/search",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResultModel(BaseModel):
    doc_id: str
    score: float
    cosine_sim: float
    overlap_ratio: float
    len_score: float
    overlap_keywords: List[str]
    preview: str
    category: str
    reason: str


class SearchResponse(BaseModel):
    results: List[SearchResultModel]


class StatsResponse(BaseModel):
    documents: int
    embeddings: int


@app.on_event("startup")
async def startup_event() -> None:
    """Load index at startup so search is fast."""

    try:
        index, ids = index_manager.load_index()
    except FileNotFoundError as exc:
        # Index not built yet; log and continue. /search will just return empty.
        print(f"[WARN] {exc}")
        app.state.search_engine = None
        return

    app.state.search_engine = SearchEngine(index=index, id_mapping=ids)
    print(f"[INFO] Loaded FAISS index with {index.ntotal} vectors")


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> Dict[str, Any]:
    if app.state.search_engine is None:
        return {"results": []}

    engine: SearchEngine = app.state.search_engine
    results = engine.search(query=req.query, top_k=req.top_k)
    return {"results": results_to_dict(results)}


@app.get("/docs/{doc_id}")
async def get_document(doc_id: str) -> Dict[str, Any]:
    doc = cache_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(doc.filepath)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        text = ""

    return {
        "doc_id": doc.doc_id,
        "filepath": doc.filepath,
        "category": doc.category,
        "length_tokens": doc.length_tokens,
        "text": text,
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> Dict[str, int]:
    stats = cache_manager.get_stats()
    return stats


