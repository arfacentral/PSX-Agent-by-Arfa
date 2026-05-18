@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  python -m venv .venv
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
)

echo Installing/updating required packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

set USERPROFILE=%CD%
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo.
echo Opening PSX Agent by Arfa GUI...
echo Use this link in your browser: http://127.0.0.1:8504
echo.
".venv\Scripts\python.exe" -m streamlit run gui/app.py --server.address 127.0.0.1 --server.port 8504 --server.headless true
