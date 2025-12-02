import requests
import json
from src.config.config import Config
from src.models.base import db
from src.models.user import User
from main import create_app

BASE_URL = "http://localhost:5000/api/medical-chatbot"

def setup_test_user():
    """Create a test user with a name directly in DB"""
    app = create_app()
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(email="test_user_named@example.com").first()
        if not user:
            user = User(
                full_name="Nguyễn Văn A",
                email="test_user_named@example.com",
                password_hash="hashed_password",
                language_preference="vi",
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {user.full_name} (ID: {user.user_id})")
            return user.user_id
        else:
            print(f"User exists: {user.full_name} (ID: {user.user_id})")
            return user.user_id

def test_greeting(user_id):
    """Test if chatbot greets by name"""
    print("\n" + "="*60)
    print("TEST: Chatbot Greeting")
    print("="*60)
    
    # Send a question
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "user_id": user_id,
            "question": "Xin chào, tôi bị đau đầu"
        }
    )
    
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        answer = resp.json()['answer']
        print(f"Answer: {answer[:100]}...")
        
        if "Nguyễn Văn A" in answer:
            print("✅ PASS: Chatbot greeted user by name!")
        else:
            print("⚠️ WARNING: Chatbot did not use the name.")
    else:
        print("❌ ERROR: Request failed")

if __name__ == "__main__":
    try:
        user_id = setup_test_user()
        test_greeting(user_id)
    except Exception as e:
        print(f"Error: {e}")
