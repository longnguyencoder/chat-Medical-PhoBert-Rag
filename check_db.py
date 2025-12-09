from src import create_app
from src.models.base import db
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.user import User

app = create_app()

with app.app_context():
    print("-" * 50)
    print("🔍 CHECKING DATABASE CONTENT")
    print("-" * 50)

    # 1. Check User 5
    user = User.query.get(5)
    if user:
        print(f"✅ User 5 found: {user.email}")
    else:
        print("❌ User 5 NOT found!")

    # 2. Check Conversation 32
    conv = Conversation.query.get(32)
    if conv:
        print(f"✅ Conversation 32 found!")
        print(f"   - Title: {conv.title}")
        print(f"   - User ID: {conv.user_id}")
        print(f"   - Started At: {conv.started_at}")
    else:
        print("❌ Conversation 32 NOT found!")

    # 3. List all conversations for User 5
    print("\n📋 All conversations for User 5:")
    user_convs = Conversation.query.filter_by(user_id=5).all()
    if user_convs:
        for c in user_convs:
            msg_count = Message.query.filter_by(conversation_id=c.conversation_id).count()
            print(f"   - ID: {c.conversation_id} | Title: {c.title} | Messages: {msg_count}")
    else:
        print("   (No conversations found)")

    print("-" * 50)
