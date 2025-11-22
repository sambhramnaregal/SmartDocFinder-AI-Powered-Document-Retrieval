# SmartDocFinder – AI-Powered Document Retrieval

This project is a lightweight embedding-based search engine over a folder of text documents, with:

- Sentence-transformer embeddings with caching (SQLite)
- FAISS vector index (cosine similarity via inner product)
- FastAPI retrieval API with ranking explanations
- Modern React + TailwindCSS UI (Vite) for an attractive search experience

## Overview

**Backend (Python/FastAPI)**

- Preprocesses `.txt` documents from a folder, cleans text, and computes a SHA-256 hash
- Caches document metadata and embeddings in SQLite (`data/cache.db`)
- Builds a FAISS `IndexFlatIP` index over L2-normalized embeddings (`data/index.faiss` + `data/index_meta.json`)
- Exposes `/search`, `/docs/{doc_id}`, and `/stats` endpoints via FastAPI
- Computes a composite ranking score and explanations for each result:
  - Cosine similarity between embeddings
  - Keyword overlap ratio between query and document
  - Light document length normalization

**Frontend (React/Vite/Tailwind)**

- Full-screen, modern UI with gradient background
- Central search bar with subtle glassmorphism styling
- Result cards showing:
  - Doc id and category
  - Score bar + numeric score
  - Preview text
  - Overlapping keywords as chips
  - Natural-language explanation of why it matched
- Expandable panel with metric bars (cosine similarity, overlap ratio, length normalization)

## Folder structure

```text
.
├── backend/
│   ├── requirements.txt
│   └── src/
│       ├── __init__.py
│       ├── api.py
│       ├── cache_manager.py
│       ├── embedder.py
│       ├── index_manager.py
│       ├── preprocess.py
│       └── search_engine.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── tailwind.config.cjs
│   ├── vite.config.mjs
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       ├── main.jsx
│       └── components/
│           ├── ExplanationPanel.jsx
│           ├── ResultCard.jsx
│           └── SearchPage.jsx
├── data/
│   ├── docs/              # place your .txt documents here
│   ├── cache.db           # SQLite cache (auto-created)
│   ├── index.faiss        # FAISS index (auto-created)
│   └── index_meta.json    # FAISS id mapping (auto-created)
└── README.md
```

## How caching works

- Each document is cleaned (lowercased, HTML tags stripped, whitespace normalized).
- A SHA-256 hash of the cleaned text is computed and stored in the `documents` table.
- Embeddings are stored in the `embeddings` table as serialized NumPy arrays.
- On each preprocessing run:
  - If a document is new or its hash has changed, a fresh embedding is computed and upserted.
  - If the hash is unchanged, the cached embedding is reused (no recomputation).
- After updating embeddings, a FAISS index is rebuilt from all cached embeddings and written to disk.

SQLite schema (simplified):

- `documents(doc_id, filepath, category, length_tokens, sha256_hash)`
- `embeddings(doc_id, embedding BLOB, updated_at)`

`doc_id` is the relative path of the `.txt` file under `data/docs` (e.g. `sci.space/12345.txt`).

## Backend setup

From the `backend` directory:

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

### Prepare documents

Create `data/docs` and place `.txt` files there. For example, you can export 20 Newsgroups or any other corpus into plain-text files arranged by category:

```text
data/docs/
  sci.space/
    doc_001.txt
    doc_002.txt
  comp.graphics/
    doc_003.txt
    ...
```

### (Optional) Download the 20 Newsgroups dataset

You can automatically download and export the 20 Newsgroups training split into `data/docs` using the helper script (requires `scikit-learn`, already listed in `backend/requirements.txt`):

```bash
cd backend
python -m src.download_20newsgroups --out-dir ..\data\docs
```

This will create subfolders by newsgroup category and write each post as a `.txt` file.

### Run preprocessing + index build

From the `backend` directory:

```bash
# Using default docs directory ../data/docs
python -m src.preprocess

# Or specify a custom docs directory
python -m src.preprocess --docs-dir ..\\data\\docs
```

This will:

1. Initialize `data/cache.db` (if not present).
2. Scan all `.txt` files under the docs directory.
3. Upsert document metadata and compute hashes.
4. Generate embeddings only for new/changed documents.
5. Build a FAISS index and save it to `data/index.faiss` + `data/index_meta.json`.

### Start the FastAPI server

Still from the `backend` directory, after preprocessing (local dev):

```bash
uvicorn src.api:app --reload --port 8000
```

For **Render** or any host where the working directory is the repo root, use:

```bash
uvicorn backend.src.api:app --host 0.0.0.0 --port $PORT
```

where `$PORT` is provided by the host (Render defaults to 10000).

FastAPI will:

- Load the FAISS index on startup.
- Serve the following endpoints:
  - `POST /search` – semantic search with explanations
  - `GET /docs/{doc_id}` – full document text and metadata
  - `GET /stats` – simple counts of documents and embeddings

#### Example: `/search` request

```json
{
  "query": "quantum physics basics",
  "top_k": 5
}
```

#### Example: `/search` response (shape)

```json
{
  "results": [
    {
      "doc_id": "sci.space/12345.txt",
      "score": 0.88,
      "cosine_sim": 0.91,
      "overlap_ratio": 0.42,
      "len_score": 0.76,
      "overlap_keywords": ["quantum", "particle"],
      "preview": "quantum theory is concerned with...",
      "category": "sci.space",
      "reason": "Semantic match with overlapping keywords: quantum, particle."
    }
  ]
}
```

## Frontend setup (React + Tailwind)

From the `frontend` directory:

```bash
npm install
npm run dev
```

By default, Vite will start the dev server on `http://localhost:5173`.

Make sure the FastAPI backend is running on `http://localhost:8000` (as shown above).

### Frontend behavior

- Typing a query and hitting **Search** will send a `POST /search` request to the backend.
- Results are displayed as animated cards showing:
  - Document id & category chip
  - Composite score with a gradient score bar
  - Text preview
  - Overlapping query keywords as chips
  - A short explanation sentence
- Clicking **"Show ranking details"** expands a panel displaying:
  - Separate bars and numeric values for cosine similarity, keyword overlap ratio, and length normalization
  - A textual explanation of how the final score is computed

## Design choices

- **Efficiency**
  - Uses a single sentence-transformer model (`all-MiniLM-L6-v2`) cached in memory.
  - Embeddings are cached in SQLite and only recomputed when a document’s hash changes.
  - FAISS index is persisted to disk and only rebuilt after preprocessing.

- **Ranking & explanation**
  - FAISS provides fast approximate nearest neighbors via inner product on L2-normalized embeddings (cosine similarity).
  - The final score is a weighted combination of:
    - `cosine_sim` (0.7)
    - `overlap_ratio` (0.2)
    - `len_score` (0.1)
  - Overlapping keywords and component scores are surfaced in the API and highlighted in the UI.

- **UI/UX**
  - React + Vite for a fast, modern frontend experience.
  - TailwindCSS for rapid styling: gradients, rounded cards, and responsive layout.
  - Clear visual feedback with score bars, chips, and explanation text, making the system more interpretable and demo-friendly.

## Next steps / Extensions

- Add query expansion (e.g., synonyms via WordNet or embedding neighbors).
- Add batch preprocessing with multiprocessing for larger corpora.
- Persist the FAISS index in a more advanced backend (e.g., disk-based IVF index) for very large datasets.
- Add evaluation scripts with a small set of test queries and relevance labels.
