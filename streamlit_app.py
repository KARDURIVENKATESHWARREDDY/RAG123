import streamlit as st
from backend.database import load_faq_db
from backend.search_engine import RAGEngine

st.set_page_config(page_title="ShopGlide RAG Support", layout="wide")

st.title("ShopGlide RAG Customer Support Chatbot")

st.markdown(
    "This Streamlit app runs the ShopGlide FAQ assistant directly inside Streamlit using the same backend data and retrieval logic. "
    "It works without requiring a separate FastAPI server or external embedding."
)

@st.cache_data
def get_engine():
    faq_items = load_faq_db()
    engine = RAGEngine(mode="mock")
    engine.initialize(faq_items)
    return engine

engine = get_engine()

if "history" not in st.session_state:
    st.session_state["history"] = []
if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""


def submit_question():
    question = st.session_state["user_query"].strip()
    if not question:
        return

    results = engine.search(question, top_k=3)
    response = engine.generate_answer(question, results)
    st.session_state["history"].append({
        "question": question,
        "response": response,
        "results": results,
    })
    st.session_state["user_query"] = ""


def set_sample_question(item):
    st.session_state["user_query"] = item

with st.sidebar:
    st.header("Ask a question")
    st.text_input(
        "Type your question here",
        key="user_query",
        on_change=submit_question,
        help="Press Enter to submit your question.",
    )
    st.button("Send", on_click=submit_question)

    st.markdown("---")
    st.markdown("### Sample questions")

    sample_questions = [
        "What payment methods do you accept?",
        "How can I request a refund?",
        "How do I track my order?",
        "How do I enable two-factor authentication?",
        "Can ShopGlide integrate with Shopify?",
    ]
    for idx, item in enumerate(sample_questions):
        st.button(item, key=f"sample_{idx}", on_click=set_sample_question, args=(item,))

    st.markdown("---")
    st.markdown(
        "This app uses the same FAQ dataset and TF-IDF retrieval logic as the repository's backend. "
        "For the full React frontend experience, run the backend locally and visit `http://localhost:8000`."
    )

st.markdown("### Recent questions")
recent = list(reversed(st.session_state["history"]))[:5]
if recent:
    for entry in recent:
        st.write(f"- {entry['question']}")
else:
    st.info("No recent questions yet. Ask one from the sidebar.")

st.markdown("### Chat history")
if not st.session_state.history:
    st.info("Ask a question from the sidebar to begin. The app will find the most relevant FAQ answers and show sources.")
else:
    for entry in reversed(st.session_state.history):
        st.markdown(f"**You:** {entry['question']}")
        response = entry["response"]
        if response["refused"]:
            st.warning(response["answer"])
        else:
            st.markdown(response["answer"])

        if entry["results"]:
            with st.expander("Sources"):
                for idx, result in enumerate(entry["results"], start=1):
                    document = result["document"]
                    st.markdown(
                        f"**{idx}. {document['question']}**  \
" 
                        f"Category: {document['category']}  \
" 
                        f"Score: {result['score']:.2f}"
                    )

st.markdown("---")
st.subheader("FAQ topics covered")
faq = load_faq_db()
categories = sorted({item["category"] for item in faq})
for category in categories:
    with st.expander(category.title()):
        for item in [x for x in faq if x["category"] == category]:
            st.markdown(f"- **{item['question']}**")

