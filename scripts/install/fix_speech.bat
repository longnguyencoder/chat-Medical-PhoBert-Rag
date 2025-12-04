@echo off
REM Fix Speech-to-Text - Install Whisper to Current Environment
REM =============================================================

echo ========================================
echo FIXING SPEECH-TO-TEXT
echo ========================================
echo.

echo [1/3] Checking current Python...
python -c "import sys; print('Python:', sys.executable)"
echo.

echo [2/3] Installing openai-whisper to current environment...
python -m pip install openai-whisper ffmpeg-python
echo.

echo [3/3] Verifying installation...
python -c "import whisper; print('✓ Whisper installed successfully!')"
echo.

echo ========================================
echo DONE!
echo ========================================
echo.
echo Please restart the server:
echo   1. Stop current server (Ctrl+C)
echo   2. Run: python main.py
echo.
pause
