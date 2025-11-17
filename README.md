# WillsShareStore - Internet Sharing Platform

A peer-to-peer internet sharing platform where users can share their internet connection and earn rewards, while others can access affordable internet.

## Features

- 🌐 **Internet Sharing**: Share your internet connection and earn money
- 🔒 **100% Anonymous**: No one can see who is sharing with them
- 💰 **Earn Money**: Sharers earn $0.30 per GB shared
- 📱 **Simple Interface**: Easy-to-use platform for both sharers and users
- 🇿🇼 **Zimbabwe Focus**: Optimized for Zimbabwe market with ZOL-based pricing

## Pricing

Based on ZOL unlimited data pricing:
- 1GB: $1.50
- 5GB: $6.50
- 10GB: $12.00
- Unlimited: $13.00/month

## Revenue Model

**You earn** $0.20 per GB transferred through the platform:
- Users pay $0.50 per GB
- Sharers earn $0.30 per GB
- Platform (you) earns $0.20 per GB

## Setup for Render.com

1. **Create account on Render.com**

2. **Create a new Web Service**
   - Connect your GitHub repository
   - Select Python environment
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. **Environment Variables** (Add in Render dashboard):
