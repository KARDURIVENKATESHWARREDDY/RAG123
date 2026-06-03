import time
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

from database import load_faq_db
from search_engine import RAGEngine
from evaluator import run_evaluation, load_evaluation_history

app = FastAPI(title="ShopGlide Customer Support RAG Bot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store session chatbot statistics in-memory
session_stats = {
    "total_queries": 0,
    "total_refusals": 0,
    "latencies": [],
    "modes": {"mock": 0, "ollama": 0}
}

# Request and Response schemas
class ChatRequest(BaseModel):
    message: str
    mode: str = "mock" # "mock" or "ollama"
    embedding_model: Optional[str] = "nomic-embed-text"
    llm_model: Optional[str] = "llama3"

class FAQItem(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    tags: List[str]

class EvaluateRequest(BaseModel):
    mode: str = "mock"
    embedding_model: Optional[str] = "nomic-embed-text"
    llm_model: Optional[str] = "llama3"

@app.on_event("startup")
def startup_event():
    # Make sure FAQ DB is generated on start
    load_faq_db()

@app.get("/api/status")
def get_status():
    engine = RAGEngine(mode="ollama")
    ollama_connected = engine.ollama_engine.check_connection()
    
    models = []
    if ollama_connected:
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
            
    return {
        "status": "online",
        "ollama": {
            "connected": ollama_connected,
            "url": "http://localhost:11434",
            "available_models": models
        }
    }

@app.get("/api/faq", response_model=List[FAQItem])
def get_faqs():
    try:
        return load_faq_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def process_chat(req: ChatRequest):
    start_time = time.perf_counter()
    
    faq_items = load_faq_db()
    
    # Initialize Engine with specified parameters
    engine = RAGEngine(
        mode=req.mode,
        embedding_model=req.embedding_model,
        llm_model=req.llm_model
    )
    
    try:
        engine.initialize(faq_items)
    except Exception as e:
        if req.mode == "ollama":
            # Gracefully fallback to mock
            print(f"Ollama initialization failed: {e}. Falling back to mock.")
            engine = RAGEngine(mode="mock")
            engine.initialize(faq_items)
        else:
            raise HTTPException(status_code=500, detail=f"Failed to initialize search engine: {str(e)}")
            
    retrieval_start = time.perf_counter()
    # Search documents
    retrieved = engine.search(req.message, top_k=3)
    retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
    
    generation_start = time.perf_counter()
    # Generate answer
    response = engine.generate_answer(req.message, retrieved)
    generation_ms = (time.perf_counter() - generation_start) * 1000
    
    total_ms = (time.perf_counter() - start_time) * 1000
    
    # Update Session Analytics
    session_stats["total_queries"] += 1
    if response.get("refused", False):
        session_stats["total_refusals"] += 1
    session_stats["latencies"].append(total_ms)
    session_stats["modes"][response["engine"]] = session_stats["modes"].get(response["engine"], 0) + 1
    
    return {
        "answer": response["answer"],
        "sources": response["sources"],
        "refused": response["refused"],
        "engine": response["engine"],
        "confidence": response["confidence"],
        "latency_ms": {
            "retrieval": retrieval_ms,
            "generation": generation_ms,
            "total": total_ms
        }
    }

@app.get("/api/analytics")
def get_analytics():
    # Load past benchmark metrics from evaluator history
    history = load_evaluation_history()
    
    # Calculate live session average stats
    avg_session_latency = 0.0
    if session_stats["latencies"]:
        avg_session_latency = sum(session_stats["latencies"]) / len(session_stats["latencies"])
        
    refusal_rate = 0.0
    if session_stats["total_queries"] > 0:
        refusal_rate = session_stats["total_refusals"] / session_stats["total_queries"]
        
    return {
        "live_session": {
            "total_queries": session_stats["total_queries"],
            "total_refusals": session_stats["total_refusals"],
            "refusal_rate": refusal_rate,
            "average_latency_ms": avg_session_latency,
            "mode_distribution": session_stats["modes"]
        },
        "evaluation_history": history,
        "latest_evaluation": history[-1] if history else None
    }

@app.post("/api/evaluate")
def trigger_evaluation(req: EvaluateRequest):
    try:
        results = run_evaluation(
            mode=req.mode,
            embedding_model=req.embedding_model,
            llm_model=req.llm_model
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# Mount static build folder of the React frontend, if it exists
frontend_dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")
    print(f"Mounted production frontend static files from: {frontend_dist_path}")
else:
    print(f"Frontend dist folder not found at {frontend_dist_path}. Run frontend build step to bundle frontend.")
