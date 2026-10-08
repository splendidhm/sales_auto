@echo off
setlocal
cd /d "%~dp0.."
"%~dp0..\.venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
exit /b %errorlevel%
