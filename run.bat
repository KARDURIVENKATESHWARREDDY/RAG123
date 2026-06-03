@echo off
echo ========================================================
echo       ShopGlide Support RAG Chatbot Launcher
echo ========================================================
echo.

:: Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python.
    pause
    exit /b 1
)

:: Install/update Python requirements
echo [1/3] Verifying python backend dependencies...
python -m pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)

:: Check if frontend dist folder exists, compile if missing
if not exist "frontend\dist" (
    echo [2/3] Frontend dist not found. Building React client...
    cd frontend
    call npm install
    call npm run build
    cd ..
) else (
    echo [2/3] Frontend production build verified!
)

:: Launch browser in background
echo [3/3] Starting backend API and client server...
echo.
echo ========================================================
echo   ShopGlide is running at: http://localhost:8000
echo   To stop the server, press Ctrl+C in this terminal.
echo ========================================================
echo.

start "" "http://localhost:8000"

:: Start Uvicorn
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
