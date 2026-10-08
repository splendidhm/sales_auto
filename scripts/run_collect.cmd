@echo off
setlocal
cd /d "%~dp0.."
"%~dp0..\.venv\Scripts\python.exe" -m affiliate_hub.cli collect --provider mock
exit /b %errorlevel%
