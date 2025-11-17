from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_sharer = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    tokens = db.Column(db.Float, default=0.0)  # For users
    earnings = db.Column(db.Float, default=0.0)  # For sharers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sharing_sessions = db.relationship('SharingSession', backref='sharer', lazy=True, foreign_keys='SharingSession.sharer_id')
    usage_sessions = db.relationship('SharingSession', backref='user', lazy=True, foreign_keys='SharingSession.user_id')
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SharingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    sharer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Anonymous connection - no personal info shared
    connection_token = db.Column(db.String(64), unique=True, nullable=False)
    
    # Data tracking
    data_used_mb = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(SharingSession, self).__init__(**kwargs)
        self.session_id = secrets.token_urlsafe(32)
        self.connection_token = secrets.token_urlsafe(32)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'purchase', 'earning', 'withdrawal'
    amount = db.Column(db.Float, nullable=False)
    tokens = db.Column(db.Float)  # For token purchases
    description = db.Column(db.String(256))
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminEarnings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_earnings = db.Column(db.Float, default=0.0)
    total_transactions = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
