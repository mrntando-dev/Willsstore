import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Fix PostgreSQL URL format
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or 'postgresql://ntando_user:hE9jYl2QVozF7iURwVXqr1gTsFLftbiP@dpg-d4djg0jipnbc73a3tq80-a/ntando'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Token pricing
    TOKEN_PRICE_PER_GB = 0.50  # USD per GB
    SHARER_EARNINGS_PER_GB = 0.30  # USD per GB shared
    YOUR_COMMISSION_PER_GB = 0.20  # Your earnings per GB
    
    # Zimbabwe pricing (based on ZOL unlimited at $13)
    ZIMBABWE_UNLIMITED_PRICE = 13.00  # Monthly unlimited
    ZIMBABWE_TOKEN_PACKAGES = {
        '1GB': 1.50,
        '5GB': 6.50,
        '10GB': 12.00,
        'UNLIMITED': 13.00  # Monthly
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Supported countries
    SUPPORTED_COUNTRIES = ['Zimbabwe']
    COMING_SOON_MESSAGE = "Coming soon to your country!"
