import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///willsshare.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
