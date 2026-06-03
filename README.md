# ShopGlide RAG Customer Support Chatbot & Analytics Dashboard

A secure, internal customer support chatbot demo designed to answer questions from a curated FAQ database (Billing, Shipping, Account Security, Integrations, Partners) using RAG. Features a clean, modern, dark glassmorphism UI, detailed source tagging, and a comprehensive retrieval/generation analytics dashboard.

---

## Features
- **Semantic Retrieval**: Custom vector-space matcher using stopword-filtered TF-IDF cosine similarity.
- **Ollama AI Integration**: Full fallback support to dense vector similarity embeddings (`nomic-embed-text` via `/api/embed`) and LLM answer synthesis (`llama3` via `/api/chat`).
- **Mock Mode**: Works immediately with zero external dependencies or API keys.
- **Refusal System**: Politely rejects questions that lie outside the scope of the knowledge base.
- **Analytics Panel**: Tracks live query counts, average latencies, refusal rates, and runs automatic test benchmarks (MRR, Recall@3, Precision@1, Faithfulness) rendered in interactive, custom SVG line graphs.

---

## Directory Structure
- `backend/`: FastAPI API server, TF-IDF indexing logic, data generator, and evaluators.
  - `database.py`: Manages the FAQ JSON source.
  - `search_engine.py`: Handles vector indexing and Ollama connectors.
  - `evaluator.py`: Automatic benchmark evaluator runner.
  - `app.py`: REST endpoint routing and static client server.
  - `test_backend.py`: Python unit tests pipeline.
- `frontend/`: React + Vite client. Styled with Vanilla CSS (Dark Glassmorphic Theme).
  - `src/components/ChatWindow.jsx`: Customer support chat client.
  - `src/components/AnalyticsPanel.jsx`: Live session charts & evaluation benchmarks.
  - `src/components/SourceCard.jsx`: referenced document viewer details modal.

---

## Quick Start (Local Execution)

### Windows
Double-click `run.bat` or run:
```cmd
run.bat
```

### Linux / macOS
Grant execution permissions and execute:
```bash
chmod +x run.sh
./run.sh
```

The launcher will verify python packages, compile the frontend, open your browser, and run the server at **[http://localhost:8000](http://localhost:8000)**.

---

## Simple Commands & Scripts

All commands should be executed from the root workspace directory.

### 1. Generating FAQ Data
The FAQ database is auto-generated on startup, but you can manually recreate or inspect it via:
```bash
python backend/database.py
```
This writes the dataset to `backend/data/faq_kb.json`.

### 2. Running Automated Tests
Run unit tests to verify database loading, search accuracy, and API controllers:
```bash
python backend/test_backend.py
```

### 3. Running Evaluator Benchmarks
Trigger the automated evaluator set (20 queries containing expected answers and out-of-bounds questions) to test Precision, Recall, MRR, Refusal Accuracy, and Faithfulness:
```bash
python backend/evaluator.py
```
Results will print to your terminal and log a record to `backend/data/eval_history.json`, which updates the charts on the dashboard.

---

## Running with Docker

You can package and execute the entire stack inside Docker. The configuration supports hot-connecting to an Ollama server running on your host machine.

1. Build and launch the container:
   ```bash
   docker compose up --build
   ```
2. Open **[http://localhost:8000](http://localhost:8000)**.

---

## Ollama AI Integration (Optional)

To enable dense semantic search and LLM synthesis:
1. Download and run [Ollama](https://ollama.com).
2. Pull the embedding model and LLM:
   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3
   ```
3. Once running, the app header status bar will show **Ollama: Online**. You can toggle the search mode to **Ollama AI** in the settings side panel.
