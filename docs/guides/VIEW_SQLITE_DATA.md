# Hướng Dẫn Xem Dữ Liệu SQLite
# ================================

## 📍 Vị Trí Database

**File SQLite:** `instance/chatbot.db`
**Full path:** `C:\Users\PT COMPUTER\Documents\GitHub\chat-Medical-PhoBert-Rag\instance\chatbot.db`

---

## 🛠️ Cách 1: DB Browser for SQLite (GUI - Khuyến nghị) ⭐

### Bước 1: Download & Install
- **Link:** https://sqlitebrowser.org/dl/
- **File:** DB.Browser.for.SQLite-v3.12.2-win64.msi
- **Size:** ~15MB
- **Free:** Open source

### Bước 2: Mở Database
1. Mở DB Browser
2. Click "Open Database"
3. Navigate to: `instance/chatbot.db`
4. Click "Open"

### Bước 3: Xem Dữ Liệu
- **Browse Data tab:** Xem records trong tables
- **Execute SQL tab:** Chạy SQL queries
- **Database Structure tab:** Xem schema

### Ví Dụ Queries:
```sql
-- Xem tất cả users
SELECT * FROM users;

-- Xem conversations
SELECT * FROM conversations ORDER BY started_at DESC LIMIT 10;

-- Xem messages trong conversation
SELECT * FROM messages WHERE conversation_id = 44;

-- Count messages by type
SELECT message_type, COUNT(*) FROM messages GROUP BY message_type;
```

---

## 🛠️ Cách 2: Python Script (Quick View)

### Script: `scripts/database/view_sqlite_data.py`

```python
import sqlite3
import pandas as pd

# Connect to database
db_path = 'instance/chatbot.db'
conn = sqlite3.connect(db_path)

# List all tables
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("📊 Tables in database:")
print(tables)
print()

# View users
print("👥 Users:")
users = pd.read_sql("SELECT * FROM users LIMIT 5", conn)
print(users)
print()

# View conversations
print("💬 Recent Conversations:")
convs = pd.read_sql("""
    SELECT conversation_id, user_id, title, started_at 
    FROM conversations 
    ORDER BY started_at DESC 
    LIMIT 5
""", conn)
print(convs)
print()

# View messages
print("📝 Recent Messages:")
msgs = pd.read_sql("""
    SELECT message_id, conversation_id, sender, message_text, message_type 
    FROM messages 
    ORDER BY sent_at DESC 
    LIMIT 5
""", conn)
print(msgs)

conn.close()
```

**Chạy:**
```bash
python scripts/database/view_sqlite_data.py
```

---

## 🛠️ Cách 3: SQLite Command Line

### Mở SQLite CLI:
```bash
# Cài sqlite3 (nếu chưa có)
# Download: https://www.sqlite.org/download.html

# Mở database
sqlite3 instance/chatbot.db
```

### Commands:
```sql
-- List tables
.tables

-- View table schema
.schema users

-- Query data
SELECT * FROM users;

-- Pretty print
.mode column
.headers on
SELECT * FROM conversations LIMIT 5;

-- Export to CSV
.mode csv
.output conversations.csv
SELECT * FROM conversations;
.output stdout

-- Exit
.quit
```

---

## 🛠️ Cách 4: VS Code Extension

### Extension: SQLite Viewer
1. Mở VS Code
2. Install extension: "SQLite Viewer" by Florian Klampfer
3. Right-click `instance/chatbot.db`
4. Select "Open Database"

---

## 📊 Useful Queries

### Users & Authentication:
```sql
-- All users
SELECT user_id, email, full_name, is_verified, created_at FROM users;

-- Verified users only
SELECT * FROM users WHERE is_verified = 1;

-- Recent registrations
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
```

### Conversations:
```sql
-- All conversations
SELECT * FROM conversations ORDER BY started_at DESC;

-- Conversations by user
SELECT * FROM conversations WHERE user_id = 3;

-- Conversation with message count
SELECT 
    c.conversation_id,
    c.title,
    COUNT(m.message_id) as message_count
FROM conversations c
LEFT JOIN messages m ON c.conversation_id = m.conversation_id
GROUP BY c.conversation_id;
```

### Messages:
```sql
-- All messages
SELECT * FROM messages ORDER BY sent_at DESC LIMIT 20;

-- Messages in conversation
SELECT * FROM messages WHERE conversation_id = 44;

-- Voice messages only
SELECT * FROM messages WHERE message_type = 'voice';

-- Message statistics
SELECT 
    message_type,
    COUNT(*) as count
FROM messages
GROUP BY message_type;
```

### OTP (Email Verification):
```sql
-- Recent OTPs
SELECT * FROM otp ORDER BY created_at DESC LIMIT 10;

-- Active OTPs
SELECT * FROM otp WHERE is_used = 0 AND expires_at > datetime('now');
```

---

## 🔍 Database Schema

### Tables:
- `users` - User accounts
- `conversations` - Chat conversations
- `messages` - Chat messages
- `otp` - Email verification codes
- `notifications` - User notifications

### Relationships:
```
users (1) ──→ (N) conversations
conversations (1) ──→ (N) messages
users (1) ──→ (N) otp
users (1) ──→ (N) notifications
```

---

## 💡 Tips

1. **Backup before editing:**
   ```bash
   copy instance\chatbot.db instance\chatbot_backup.db
   ```

2. **Don't edit directly in production** - Use migrations

3. **Use transactions** when making changes:
   ```sql
   BEGIN TRANSACTION;
   -- Your changes
   COMMIT;
   -- or ROLLBACK if error
   ```

4. **Check file size:**
   ```bash
   dir instance\chatbot.db
   ```

---

## 🚀 Quick Commands

```bash
# View database info
python -c "import sqlite3; conn=sqlite3.connect('instance/chatbot.db'); print('Tables:', [t[0] for t in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])"

# Count records
python -c "import sqlite3; conn=sqlite3.connect('instance/chatbot.db'); print('Users:', conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]); print('Conversations:', conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]); print('Messages:', conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0])"
```
