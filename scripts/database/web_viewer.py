"""
Simple Web Viewer for SQLite Database
======================================
Flask app to view SQLite data in browser
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join('instance', 'chatbot.db')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SQLite Database Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .section {
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        .tab {
            padding: 10px 20px;
            background: #e0e0e0;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .tab.active {
            background: #4CAF50;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗄️ SQLite Database Viewer</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="users-count">-</div>
                <div class="stat-label">Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="conversations-count">-</div>
                <div class="stat-label">Conversations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="messages-count">-</div>
                <div class="stat-label">Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="voice-count">-</div>
                <div class="stat-label">Voice Messages</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('users')">👥 Users</button>
            <button class="tab" onclick="showTab('conversations')">💬 Conversations</button>
            <button class="tab" onclick="showTab('messages')">📝 Messages</button>
        </div>

        <div id="users" class="tab-content active">
            <h2>Users</h2>
            <div id="users-table"></div>
        </div>

        <div id="conversations" class="tab-content">
            <h2>Conversations</h2>
            <div id="conversations-table"></div>
        </div>

        <div id="messages" class="tab-content">
            <h2>Messages</h2>
            <div id="messages-table"></div>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        function loadData() {
            // Load stats
            fetch('/api/stats').then(r => r.json()).then(data => {
                document.getElementById('users-count').textContent = data.users;
                document.getElementById('conversations-count').textContent = data.conversations;
                document.getElementById('messages-count').textContent = data.messages;
                document.getElementById('voice-count').textContent = data.voice_messages;
            });

            // Load users
            fetch('/api/users').then(r => r.json()).then(data => {
                let html = '<table><tr><th>ID</th><th>Email</th><th>Name</th><th>Verified</th><th>Created</th></tr>';
                data.forEach(user => {
                    html += `<tr>
                        <td>${user[0]}</td>
                        <td>${user[1]}</td>
                        <td>${user[2]}</td>
                        <td>${user[3] ? '✓' : '✗'}</td>
                        <td>${user[4]}</td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('users-table').innerHTML = html;
            });

            // Load conversations
            fetch('/api/conversations').then(r => r.json()).then(data => {
                let html = '<table><tr><th>ID</th><th>User</th><th>Title</th><th>Messages</th><th>Started</th></tr>';
                data.forEach(conv => {
                    html += `<tr>
                        <td>${conv[0]}</td>
                        <td>${conv[1]}</td>
                        <td>${conv[2]}</td>
                        <td>${conv[3]}</td>
                        <td>${conv[4]}</td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('conversations-table').innerHTML = html;
            });

            // Load messages
            fetch('/api/messages').then(r => r.json()).then(data => {
                let html = '<table><tr><th>ID</th><th>Conv</th><th>Sender</th><th>Type</th><th>Message</th><th>Sent</th></tr>';
                data.forEach(msg => {
                    html += `<tr>
                        <td>${msg[0]}</td>
                        <td>${msg[1]}</td>
                        <td>${msg[2]}</td>
                        <td>${msg[3]}</td>
                        <td>${msg[4].substring(0, 50)}...</td>
                        <td>${msg[5]}</td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('messages-table').innerHTML = html;
            });
        }

        // Load data on page load
        loadData();
        // Refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conversations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    messages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE message_type = 'voice'")
    voice_messages = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'users': users,
        'conversations': conversations,
        'messages': messages,
        'voice_messages': voice_messages
    })

@app.route('/api/users')
def users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, email, full_name, is_verified, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 20
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/conversations')
def conversations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.conversation_id, c.user_id, c.title, 
               COUNT(m.message_id) as msg_count, c.started_at
        FROM conversations c
        LEFT JOIN messages m ON c.conversation_id = m.conversation_id
        GROUP BY c.conversation_id
        ORDER BY c.started_at DESC 
        LIMIT 20
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/messages')
def messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_id, conversation_id, sender, message_type, message_text, sent_at
        FROM messages 
        ORDER BY sent_at DESC 
        LIMIT 50
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🌐 SQLite Database Web Viewer")
    print("="*60)
    print(f"\n  📍 Database: {os.path.abspath(DB_PATH)}")
    print(f"  🌐 Open in browser: http://localhost:5001")
    print(f"\n  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5001)
