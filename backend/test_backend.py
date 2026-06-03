import sys
import os

# Add parent directory to path to enable direct imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import load_faq_db
from search_engine import TFIDFSearchEngine, RAGEngine
from app import process_chat, ChatRequest, get_faqs

def test_database():
    print("Testing FAQ database loading...")
    faqs = load_faq_db()
    assert len(faqs) > 0, "FAQ database should not be empty"
    assert any(f["category"] == "billing" for f in faqs), "Should contain billing FAQs"
    assert any(f["category"] == "shipping" for f in faqs), "Should contain shipping FAQs"
    assert any(f["category"] == "account security" for f in faqs), "Should contain security FAQs"
    print("OK - Database loading test passed!")

def test_tfidf_search():
    print("Testing TF-IDF Search Engine accuracy...")
    faqs = load_faq_db()
    engine = TFIDFSearchEngine()
    engine.build_index(faqs)
    
    # Exact match query
    query = "What payment methods do you accept?"
    results = engine.search(query, top_k=1)
    
    assert len(results) > 0, "Should return search results"
    assert results[0]["document"]["id"] == "bill_01", "Should match the billing payment method FAQ"
    assert results[0]["score"] > 0.5, f"Confidence score should be high for exact query, got {results[0]['score']}"
    
    # Out of scope query
    query_oob = "What is the capital of France?"
    results_oob = engine.search(query_oob, top_k=1)
    if results_oob:
        assert results_oob[0]["score"] < 0.20, f"Confidence should be low for irrelevant query, got {results_oob[0]['score']}"
    print("OK - TF-IDF Search Engine test passed!")

def test_rag_engine_mock():
    print("Testing RAG Engine mock answer generation...")
    faqs = load_faq_db()
    engine = RAGEngine(mode="mock")
    engine.initialize(faqs)
    
    # Check valid RAG response
    retrieved = engine.search("How do I track my order?")
    response = engine.generate_answer("How do I track my order?", retrieved)
    
    assert response["refused"] is False, "Should answer a standard shipping query"
    assert "track" in response["answer"].lower(), "Answer should contain tracking details"
    assert len(response["sources"]) > 0, "Answer should contain source references"
    assert response["sources"][0]["id"] == "ship_03", "Source ID should be ship_03"
    
    # Check refusal on irrelevant query
    retrieved_oob = engine.search("tell me a story about a flying dog")
    response_oob = engine.generate_answer("tell me a story about a flying dog", retrieved_oob)
    
    assert response_oob["refused"] is True, "Should refuse an irrelevant query"
    assert "sorry" in response_oob["answer"].lower(), "Refusal answer should contain standard failure message"
    assert len(response_oob["sources"]) == 0, "Refused answer should have no sources"
    print("OK - RAG Engine mock test passed!")

def test_api_endpoints():
    print("Testing API controller functions...")
    # Test FAQ loader controller
    faqs = get_faqs()
    assert len(faqs) > 0
    
    # Test Chat controller
    req = ChatRequest(message="Can I pay with PayPal?", mode="mock")
    resp = process_chat(req)
    assert resp["refused"] is False
    assert resp["engine"] == "mock"
    assert len(resp["sources"]) > 0
    assert resp["sources"][0]["id"] == "bill_01"
    assert resp["latency_ms"]["total"] > 0
    print("OK - API controller tests passed!")

if __name__ == "__main__":
    print("--- Running Backend Core Unit Tests ---")
    try:
        test_database()
        test_tfidf_search()
        test_rag_engine_mock()
        test_api_endpoints()
        print("--- ALL BACKEND TESTS PASSED SUCCESSFULLY! ---")
        sys.exit(0)
    except AssertionError as e:
        print(f"TEST ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)
