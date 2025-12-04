@echo off
REM Run Medical Chatbot Server with Global Python
REM This bypasses venv_old and uses global Python (which has Flask)

echo ========================================
echo Starting Medical Chatbot Server...
echo ========================================
echo.

REM Use global Python directly
"C:\Users\PT COMPUTER\AppData\Local\Programs\Python\Python312\python.exe" main.py

pause
