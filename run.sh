#!/bin/bash
echo "========================================================"
echo "      ShopGlide Support RAG Chatbot Launcher"
echo "========================================================"
echo ""

# Check python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed. Please install it."
    exit 1
fi

# Install dependencies
echo "[1/3] Verifying python backend dependencies..."
python3 -m pip install -r backend/requirements.txt

# Check dist
if [ ! -d "frontend/dist" ]; then
    echo "[2/3] Frontend dist not found. Building React client..."
    cd frontend
    npm install
    npm run build
    cd ..
else
    echo "[2/3] Frontend production build verified!"
fi

echo "[3/3] Starting backend API and client server..."
echo ""
echo "========================================================"
echo "  ShopGlide is running at: http://localhost:8000"
echo "  To stop the server, press Ctrl+C in this terminal."
echo "========================================================"
echo ""

# Open browser if possible
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000"
elif command -v open &> /dev/null; then
    open "http://localhost:8000"
fi

python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
