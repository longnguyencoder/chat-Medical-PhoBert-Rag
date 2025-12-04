@echo off
REM Project Cleanup Script
REM ======================
REM Tổ chức lại project structure cho gọn gàng

echo ========================================
echo PROJECT CLEANUP - Organizing Files
echo ========================================
echo.

REM Tạo thư mục mới
echo [1/4] Creating new directories...
mkdir docs\guides 2>nul
mkdir docs\setup 2>nul
mkdir docs\improvements 2>nul
mkdir docs\project 2>nul
mkdir scripts\database 2>nul
mkdir scripts\data 2>nul
mkdir scripts\testing 2>nul
mkdir scripts\install 2>nul
echo   ✓ Directories created

REM Di chuyển documentation
echo.
echo [2/4] Moving documentation files...
move DATABASE_SWITCH_GUIDE.md docs\guides\ 2>nul
move DEDUPLICATION_GUIDE.md docs\guides\ 2>nul
move LOAD_DATASET_GUIDE.md docs\guides\ 2>nul
move MEDICAL_CHATBOT_GUIDE.md docs\guides\ 2>nul
move QUICK_START_SPEECH.md docs\guides\ 2>nul
move SETUP_SPEECH_API.md docs\guides\ 2>nul
move SPEECH_API_GUIDE.md docs\guides\ 2>nul

move FIX_PYTHON_ENV.md docs\setup\ 2>nul
move INSTALL_FFMPEG.md docs\setup\ 2>nul
move database_setup.md docs\setup\ 2>nul

move PROMPT_IMPROVEMENTS.md docs\improvements\ 2>nul
move RAG_OPTIMIZATIONS.md docs\improvements\ 2>nul

move CODE_OF_CONDUCT.md docs\project\ 2>nul
move CONTRIBUTING.md docs\project\ 2>nul
move LICENSE.md docs\project\ 2>nul
move SECURITY.md docs\project\ 2>nul
echo   ✓ Documentation organized

REM Di chuyển scripts
echo.
echo [3/4] Moving script files...
move add_conversation_columns.py scripts\database\ 2>nul
move add_summary_column.py scripts\database\ 2>nul
move check_db_simple.py scripts\database\ 2>nul
move deduplicate_database.py scripts\database\ 2>nul
move deduplicate_fast.py scripts\database\ 2>nul
move fix_db_direct.py scripts\database\ 2>nul
move fix_message_type.py scripts\database\ 2>nul
move force_fix_db.py scripts\database\ 2>nul
move migrate_notifications.py scripts\database\ 2>nul
move migrate_to_postgresql.py scripts\database\ 2>nul
move update_schema.py scripts\database\ 2>nul
move verify_db.py scripts\database\ 2>nul

move load_csv_dataset.py scripts\data\ 2>nul
move load_excel_dataset.py scripts\data\ 2>nul
move load_huggingface_dataset.py scripts\data\ 2>nul
move preview_excel.py scripts\data\ 2>nul

move demo_speech_service.py scripts\testing\ 2>nul
move evaluate_chatbot.py scripts\testing\ 2>nul
move test_cache.py scripts\testing\ 2>nul
move test_hybrid_search.py scripts\testing\ 2>nul
move test_postgres_connection.py scripts\testing\ 2>nul
move test_whisper_quick.py scripts\testing\ 2>nul
move verify_chromadb.py scripts\testing\ 2>nul

move fix_speech.bat scripts\install\ 2>nul
move install_ffmpeg.ps1 scripts\install\ 2>nul
move install_speech_dependencies.ps1 scripts\install\ 2>nul
move install_speech_dependencies.sh scripts\install\ 2>nul
move run_server.bat scripts\install\ 2>nul
echo   ✓ Scripts organized

REM Xóa files không cần
echo.
echo [4/4] Cleaning up temporary files...
del CONVERSATION_CONTEXT.md 2>nul
del CONVERSATION_SUMMARY.md 2>nul
del DEV_EMAIL_FIX.txt 2>nul
del CLEANUP_PLAN.md 2>nul
echo   ✓ Temporary files removed

echo.
echo ========================================
echo CLEANUP COMPLETE!
echo ========================================
echo.
echo Root directory now contains:
dir /b | findstr /v /i "docs scripts src tests instance data migrations venv __pycache__"
echo.
echo All files organized into:
echo   - docs/       (documentation)
echo   - scripts/    (utility scripts)
echo.
pause
