# 📁 Project Structure - Organized & Clean

## ✨ Root Directory (Gọn Gàng)

```
chat-Medical-PhoBert-Rag/
├── 📄 .env                    # Environment variables
├── 📄 .gitignore              # Git ignore rules
├── 📄 main.py                 # Application entry point
├── 📄 requirements.txt        # Python dependencies
├── 📄 README.md               # Project documentation
│
├── 📁 src/                    # Source code
├── 📁 tests/                  # Test files
├── 📁 instance/               # Database files
├── 📁 data/                   # Data files
├── 📁 migrations/             # Database migrations
│
├── 📁 docs/                   # 📚 ALL DOCUMENTATION
│   ├── guides/                # User guides
│   ├── setup/                 # Setup instructions
│   ├── improvements/          # Improvement docs
│   └── project/               # Project info
│
└── 📁 scripts/                # 🛠️ UTILITY SCRIPTS
    ├── database/              # Database scripts
    ├── data/                  # Data loading scripts
    ├── testing/               # Testing scripts
    └── install/               # Installation scripts
```

## 📚 Documentation (`docs/`)

### `docs/guides/` - User Guides
- `DATABASE_SWITCH_GUIDE.md` - Switch between SQLite/PostgreSQL
- `DEDUPLICATION_GUIDE.md` - Remove duplicate data
- `LOAD_DATASET_GUIDE.md` - Load datasets
- `MEDICAL_CHATBOT_GUIDE.md` - Chatbot usage
- `QUICK_START_SPEECH.md` - Quick start for Speech-to-Text
- `SETUP_SPEECH_API.md` - Speech API setup
- `SPEECH_API_GUIDE.md` - Complete Speech API guide

### `docs/setup/` - Setup Instructions
- `FIX_PYTHON_ENV.md` - Fix Python environment issues
- `INSTALL_FFMPEG.md` - Install ffmpeg
- `database_setup.md` - Database setup

### `docs/improvements/` - Improvement Documentation
- `PROMPT_IMPROVEMENTS.md` - Prompt engineering tips
- `RAG_OPTIMIZATIONS.md` - RAG optimization guide

### `docs/project/` - Project Information
- `CODE_OF_CONDUCT.md` - Code of conduct
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE.md` - License
- `SECURITY.md` - Security policy

## 🛠️ Scripts (`scripts/`)

### `scripts/database/` - Database Management (12 files)
- `add_conversation_columns.py` - Add conversation columns
- `add_summary_column.py` - Add summary column
- `check_db_simple.py` - Simple DB check
- `deduplicate_database.py` - Remove duplicates
- `deduplicate_fast.py` - Fast deduplication
- `fix_db_direct.py` - Direct DB fix
- `fix_message_type.py` - Fix message types
- `force_fix_db.py` - Force DB fix
- `migrate_notifications.py` - Migrate notifications
- `migrate_to_postgresql.py` - Migrate to PostgreSQL
- `update_schema.py` - Update DB schema
- `verify_db.py` - Verify database

### `scripts/data/` - Data Loading (4 files)
- `load_csv_dataset.py` - Load CSV data
- `load_excel_dataset.py` - Load Excel data
- `load_huggingface_dataset.py` - Load HuggingFace data
- `preview_excel.py` - Preview Excel files

### `scripts/testing/` - Testing & Verification (7 files)
- `demo_speech_service.py` - Demo speech service
- `evaluate_chatbot.py` - Evaluate chatbot
- `test_cache.py` - Test caching
- `test_hybrid_search.py` - Test hybrid search
- `test_postgres_connection.py` - Test PostgreSQL
- `test_whisper_quick.py` - Quick Whisper test
- `verify_chromadb.py` - Verify ChromaDB

### `scripts/install/` - Installation Scripts (5 files)
- `fix_speech.bat` - Fix speech dependencies
- `install_ffmpeg.ps1` - Install ffmpeg (PowerShell)
- `install_speech_dependencies.ps1` - Install speech deps (PowerShell)
- `install_speech_dependencies.sh` - Install speech deps (Bash)
- `run_server.bat` - Run server shortcut

## 🚀 Quick Commands

### Run Server
```bash
python main.py
# Or use shortcut:
scripts\install\run_server.bat
```

### Database Management
```bash
# Check database
python scripts/database/check_db_simple.py

# Fix message types
python scripts/database/fix_message_type.py

# Deduplicate data
python scripts/database/deduplicate_fast.py
```

### Load Data
```bash
# Load CSV
python scripts/data/load_csv_dataset.py

# Load from HuggingFace
python scripts/data/load_huggingface_dataset.py
```

### Testing
```bash
# Test chatbot
python scripts/testing/evaluate_chatbot.py

# Test speech
python scripts/testing/test_whisper_quick.py
```

## 📖 Documentation Quick Links

- **Getting Started:** `README.md`
- **Speech-to-Text:** `docs/guides/SPEECH_API_GUIDE.md`
- **Database Setup:** `docs/setup/database_setup.md`
- **Switch Database:** `docs/guides/DATABASE_SWITCH_GUIDE.md`

## ✅ Benefits of New Structure

- ✅ **Clean Root:** Only 6 essential files in root
- ✅ **Organized Docs:** All documentation in `docs/`
- ✅ **Grouped Scripts:** All scripts in `scripts/` by category
- ✅ **Easy Navigation:** Clear folder structure
- ✅ **Maintainable:** Easy to find and update files

---

**Last Updated:** 2025-12-04
**Organized by:** Automated cleanup script
