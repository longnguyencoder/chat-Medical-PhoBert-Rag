import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Get base directory for absolute paths
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLITE_DB_PATH = os.path.join(BASE_DIR, '..', 'instance', 'chatbot.db')
    
    # Database - Using PostgreSQL or SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_POSTGRESQL_URL', f'sqlite:///{SQLITE_DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Frontend
    FRONTEND_URL = os.getenv('FRONTEND_URL') 

    # Database connection details (for reference)
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_PORT = os.getenv('DB_PORT')
    
    # Cache settings
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 1000))  # Max entries
    CACHE_TTL_SEARCH = int(os.getenv('CACHE_TTL_SEARCH', 3600))  # 1 hour for search results
    CACHE_TTL_RESPONSE = int(os.getenv('CACHE_TTL_RESPONSE', 1800))  # 30 min for responses