import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ShopGlide RAG Support", layout="wide")

APP_URL = os.getenv("APP_URL", "http://localhost:8000")

st.title("ShopGlide RAG Customer Support Chatbot")

st.markdown(
    "This repository is built around a FastAPI backend and a React frontend. "
    "The main application is served from `backend.app` at `http://localhost:8000` after building the frontend."
)

st.info(
    "The Streamlit wrapper can be used as a deployment landing page, and it will embed the app below when the backend is reachable from this environment."
)

st.markdown("### App access")
st.markdown(
    f"*Try the hosted app at* [{APP_URL}]({APP_URL})"
)

st.markdown("### Embedded preview")
components.html(
    f"<iframe src=\"{APP_URL}\" width=100% height=900 style=\"border:none;\"></iframe>",
    height=920,
)

st.markdown("### Local run instructions")
st.code(
    """python -m pip install -r backend/requirements.txt
npm install --prefix frontend
npm run build --prefix frontend
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000"""
)

st.markdown(
    "If the embedded app does not load, ensure the FastAPI backend is running at the configured `APP_URL` and that your deployment allows iframe embedding."
)

