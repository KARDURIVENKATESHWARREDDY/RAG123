import streamlit as st

st.set_page_config(page_title="ShopGlide RAG Support", layout="wide")

st.title("ShopGlide RAG Customer Support Chatbot")

st.markdown(
    "This repository is built around a FastAPI backend and a React frontend. "
    "The main application is served from `backend.app` at `http://localhost:8000` after building the frontend."
)

st.info(
    "This Streamlit page is a lightweight deployment wrapper so the repository can launch on Streamlit sharing platforms. "
    "The full chat UI is available via the FastAPI backend and static frontend build."
)

st.markdown("### Local run instructions")
st.code(
    """python -m pip install -r backend/requirements.txt
npm install --prefix frontend
npm run build --prefix frontend
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000"""
)

st.markdown(
    "If this app is deployed on Streamlit, it may be used as a landing page while the real service runs separately.")
