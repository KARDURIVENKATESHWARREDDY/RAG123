import time
import os
import json
from database import load_faq_db
from search_engine import RAGEngine, tokenize

# Evaluation dataset: queries mapped to ground truth FAQ IDs
# If ground_truth_id is None, the query is out of scope and the bot should refuse
EVAL_DATASET = [
    {"query": "Do you accept VISA or Mastercard?", "expected_id": "bill_01"},
    {"query": "I want a refund for my order", "expected_id": "bill_02"},
    {"query": "My credit card was declined, why?", "expected_id": "bill_03"},
    {"query": "How do I download invoice PDF?", "expected_id": "bill_04"},
    {"query": "How long does standard delivery take?", "expected_id": "ship_01"},
    {"query": "Do you deliver to Canada or Europe?", "expected_id": "ship_02"},
    {"query": "Where is my package tracking code?", "expected_id": "ship_03"},
    {"query": "My package arrived broken", "expected_id": "ship_04"},
    {"query": "How to turn on two factor authentication?", "expected_id": "sec_01"},
    {"query": "I forgot my password, how to reset?", "expected_id": "sec_02"},
    {"query": "I think someone hacked my account", "expected_id": "sec_03"},
    {"query": "Can I sync ShopGlide with Shopify?", "expected_id": "int_01"},
    {"query": "Where can I find my developer API keys?", "expected_id": "int_02"},
    {"query": "How to set up webhooks?", "expected_id": "int_03"},
    {"query": "How to sign up for affiliate program?", "expected_id": "part_01"},
    {"query": "What is the gold partner discount?", "expected_id": "part_02"},
    {"query": "Can we do co-marketing webinars?", "expected_id": "part_03"},
    {"query": "What is the weather in Paris today?", "expected_id": None}, # Out of bounds
    {"query": "Who won the super bowl in 2024?", "expected_id": None}, # Out of bounds
    {"query": "Tell me a joke about robots", "expected_id": None}  # Out of bounds
]

def get_history_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "eval_history.json")

def compute_faithfulness(generated_answer, source_faq):
    if not source_faq or not generated_answer:
        return 0.0
    
    # Measure word overlap between generated answer and the source document text
    # (Excludes common English stopwords for a cleaner metric)
    stopwords = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "for", "in", "on", "at", "by", "with", "of", "your", "our", "my", "we", "you", "i"}
    
    gen_tokens = set([w for w in tokenize(generated_answer) if w not in stopwords])
    src_tokens = set([w for w in tokenize(source_faq["answer"] + " " + source_faq["question"]) if w not in stopwords])
    
    if not gen_tokens or not src_tokens:
        return 0.0
        
    # Faithfulness = fraction of generated tokens that actually exist in the source document
    intersection = gen_tokens.intersection(src_tokens)
    return float(len(intersection) / len(gen_tokens)) if gen_tokens else 0.0

def run_evaluation(mode="mock", ollama_url="http://localhost:11434", embedding_model="nomic-embed-text", llm_model="llama3"):
    faq_items = load_faq_db()
    
    # Initialize RAG Engine
    engine = RAGEngine(mode, ollama_url, embedding_model, llm_model)
    engine.initialize(faq_items)
    
    results = []
    
    total_queries = len(EVAL_DATASET)
    valid_queries = [q for q in EVAL_DATASET if q["expected_id"] is not None]
    out_of_bounds_queries = [q for q in EVAL_DATASET if q["expected_id"] is None]
    
    p1_sum = 0
    r3_sum = 0
    mrr_sum = 0
    correct_refusals = 0
    
    retrieval_latencies = []
    generation_latencies = []
    total_latencies = []
    faithfulness_scores = []
    
    for item in EVAL_DATASET:
        query = item["query"]
        expected_id = item["expected_id"]
        
        start_total = time.perf_counter()
        
        # 1. Measure retrieval
        start_retrieve = time.perf_counter()
        retrieved = engine.search(query, top_k=3)
        retrieve_time = (time.perf_counter() - start_retrieve) * 1000
        
        # 2. Measure generation
        start_gen = time.perf_counter()
        rag_response = engine.generate_answer(query, retrieved)
        gen_time = (time.perf_counter() - start_gen) * 1000
        
        total_time = (time.perf_counter() - start_total) * 1000
        
        # Track metrics
        retrieval_latencies.append(retrieve_time)
        generation_latencies.append(gen_time)
        total_latencies.append(total_time)
        
        # Compute quality metrics
        retrieved_ids = [res["document"]["id"] for res in retrieved] if retrieved else []
        
        is_refusal = rag_response.get("refused", False)
        
        # Evaluate out of bounds queries
        if expected_id is None:
            if is_refusal:
                correct_refusals += 1
            results.append({
                "query": query,
                "expected": "REFUSE",
                "retrieved": retrieved_ids,
                "refused": is_refusal,
                "correct": is_refusal,
                "latency_ms": total_time
            })
        else:
            # Evaluate standard query retrieval
            p1 = 0
            r3 = 0
            mrr = 0
            
            if retrieved_ids:
                if retrieved_ids[0] == expected_id:
                    p1 = 1
                    mrr = 1.0
                elif expected_id in retrieved_ids:
                    r3 = 1
                    rank = retrieved_ids.index(expected_id) + 1
                    mrr = 1.0 / rank
                    
                if expected_id in retrieved_ids:
                    r3 = 1 # it was retrieved in top 3
            
            p1_sum += p1
            r3_sum += r3
            mrr_sum += mrr
            
            # Evaluate generated answer faithfulness
            faithfulness = 0.0
            if not is_refusal:
                # find matching source faq
                source_faq = next((faq for faq in faq_items if faq["id"] == expected_id), None)
                faithfulness = compute_faithfulness(rag_response["answer"], source_faq)
                faithfulness_scores.append(faithfulness)
            
            results.append({
                "query": query,
                "expected": expected_id,
                "retrieved": retrieved_ids,
                "refused": is_refusal,
                "p1": p1,
                "r3": r3,
                "mrr": mrr,
                "faithfulness": faithfulness,
                "latency_ms": total_time
            })

    # Aggregates
    num_valid = len(valid_queries)
    num_oob = len(out_of_bounds_queries)
    
    avg_p1 = (p1_sum / num_valid) if num_valid else 0.0
    avg_r3 = (r3_sum / num_valid) if num_valid else 0.0
    avg_mrr = (mrr_sum / num_valid) if num_valid else 0.0
    refusal_accuracy = (correct_refusals / num_oob) if num_oob else 0.0
    
    avg_faithfulness = (sum(faithfulness_scores) / len(faithfulness_scores)) if faithfulness_scores else 0.0
    
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "engine_mode": mode,
        "total_queries": total_queries,
        "metrics": {
            "precision_at_1": float(avg_p1),
            "recall_at_3": float(avg_r3),
            "mrr": float(avg_mrr),
            "refusal_accuracy": float(refusal_accuracy),
            "answer_faithfulness": float(avg_faithfulness),
            "avg_latency_retrieval_ms": float(sum(retrieval_latencies) / total_queries),
            "avg_latency_generation_ms": float(sum(generation_latencies) / total_queries),
            "avg_latency_total_ms": float(sum(total_latencies) / total_queries)
        },
        "query_details": results
    }
    
    # Save to history file
    history_path = get_history_path()
    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []
            
    history.append(summary)
    
    # Keep only the last 15 evaluations
    if len(history) > 15:
        history = history[-15:]
        
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    return summary

def load_evaluation_history():
    history_path = get_history_path()
    if not os.path.exists(history_path):
        return []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
        
if __name__ == "__main__":
    print("Running diagnostic evaluation for mock mode...")
    results = run_evaluation(mode="mock")
    print(json.dumps(results["metrics"], indent=2))
