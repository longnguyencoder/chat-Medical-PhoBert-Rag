
import sys
import os
from sqlalchemy import create_engine, text

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.config import Config

def check_user(email):
    print(f"Checking database: {Config.SQLALCHEMY_DATABASE_URI}")
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as connection:
            # Check if Users table exists
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='Users';"))
            if not result.fetchone():
                print("Error: 'Users' table does not exist.")
                return

            # Check for the user
            query = text("SELECT * FROM Users WHERE email = :email")
            result = connection.execute(query, {"email": email})
            user = result.fetchone()
            
            if user:
                print(f"User found: {user}")
            else:
                print(f"User with email '{email}' not found.")
                
            # List all users to be sure
            print("\nAll users in database:")
            result = connection.execute(text("SELECT id, email, full_name FROM Users"))
            for row in result:
                print(row)
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    email = "giupviecgiahoang8@gmail.com"
    check_user(email)
