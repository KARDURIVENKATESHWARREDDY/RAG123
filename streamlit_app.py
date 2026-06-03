import os
import requests
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
    "The Streamlit wrapper can be used as a deployment landing page and will only embed the app when it is reachable from this environment."
)

st.markdown("### App access")
st.markdown(f"*Try the hosted app at* [{APP_URL}]({APP_URL})")

reachable = False
try:
    response = requests.get(APP_URL, timeout=3)
    reachable = response.status_code < 500
except requests.RequestException:
    reachable = False

if reachable:
    st.markdown("### Embedded preview")
    components.html(
        f"<iframe src=\"{APP_URL}\" width=100% height=900 style=\"border:none;\"></iframe>",
        height=920,
    )
else:
    st.warning(
        "The app is not reachable from the Streamlit environment. "
        "Please set `APP_URL` to the externally accessible application URL or run the FastAPI backend locally first."
    )
    st.info(
        "If you are deploying on Streamlit, use an externally reachable host URL rather than `localhost`, "
        "and verify the target allows iframe embedding."
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

