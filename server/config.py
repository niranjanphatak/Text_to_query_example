"""
Configuration management for the application.
All values are loaded from environment variables (.env file).
NO DEFAULT VALUES - all configuration must be explicitly set.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration - all values from .env, no defaults"""
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')
    DB_NAME = os.getenv('DB_NAME')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration values are set.
        Raises ValueError if any required value is missing.
        """
        required_configs = {
            'MONGO_URI': cls.MONGO_URI,
            'DB_NAME': cls.DB_NAME,
            'OPENAI_API_KEY': cls.OPENAI_API_KEY,
            'OPENAI_BASE_URL': cls.OPENAI_BASE_URL,
            'OPENAI_MODEL': cls.OPENAI_MODEL,
        }
        
        missing = [key for key, value in required_configs.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please set these in your .env file"
            )
    
    @classmethod
    def display(cls):
        """Display current configuration (safe - no sensitive data)"""
        print("=" * 60)
        print("Configuration Loaded:")
        print("=" * 60)
        print(f"MongoDB URI: {cls.MONGO_URI}")
        print(f"Database: {cls.DB_NAME}")
        print(f"OpenAI Base URL: {cls.OPENAI_BASE_URL}")
        print(f"OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"OpenAI API Key: {'*' * 20 if cls.OPENAI_API_KEY else 'NOT SET'}")
        print(f"Flask Environment: {cls.FLASK_ENV}")
        print(f"Flask Debug: {cls.FLASK_DEBUG}")
        print("=" * 60)
