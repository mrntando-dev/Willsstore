from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, SharingSession, Transaction, AdminEarnings
from config import Config
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()
    # Initialize admin earnings if not exists
    if not AdminEarnings.query.first():
        admin_earnings = AdminEarnings()
        db.session.add(admin_earnings)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html', 
                         supported_countries=Config.SUPPORTED_COUNTRIES,
                         packages=Config.ZIMBABWE_TOKEN_PACKAGES)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        country = request.form.get('country')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(email=email, country=country, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('dashboard'))
    
    flash('Invalid email or password', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        return render_template('coming_soon.html', 
                             country=current_user.country,
                             message=Config.COMING_SOON_MESSAGE)
    
    active_sessions = SharingSession.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).all()
    
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         user=current_user,
                         active_sessions=active_sessions,
                         transactions=recent_transactions,
                         packages=Config.ZIMBABWE_TOKEN_PACKAGES)

@app.route('/share')
@login_required
def share():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        flash('Service not available in your country yet', 'error')
        return redirect(url_for('dashboard'))
    
    # Create sharing session
    session = SharingSession(sharer_id=current_user.id)
    db.session.add(session)
    
    # Mark user as sharer
    if not current_user.is_sharer:
        current_user.is_sharer = True
    
    db.session.commit()
    
    return render_template('share.html', 
                         session=session,
                         earnings_per_gb=Config.SHARER_EARNINGS_PER_GB)

@app.route('/connect', methods=['GET', 'POST'])
@login_required
def connect():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        flash('Service not available in your country yet', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        connection_token = request.form.get('connection_token')
        
        session = SharingSession.query.filter_by(
            connection_token=connection_token,
            is_active=True
        ).first()
        
        if not session:
            flash('Invalid connection code', 'error')
            return redirect(url_for('connect'))
        
        if current_user.tokens <= 0:
            flash('Insufficient tokens. Please purchase tokens first.', 'error')
            return redirect(url_for('buy_tokens'))
        
        # Connect user to session
        session.user_id = current_user.id
        db.session.commit()
        
        flash('Connected successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Find available sessions (active sharers)
    available_sessions = SharingSession.query.filter_by(
        is_active=True,
        user_id=None
    ).limit(10).all()
    
    return render_template('connect.html', 
                         sessions=available_sessions,
                         user_tokens=current_user.tokens)

@app.route('/buy-tokens', methods=['GET', 'POST'])
@login_required
def buy_tokens():
    if request.method == 'POST':
        package = request.form.get('package')
        
        if package not in Config.ZIMBABWE_TOKEN_PACKAGES:
            flash('Invalid package', 'error')
            return redirect(url_for('buy_tokens'))
        
        price = Config.ZIMBABWE_TOKEN_PACKAGES[package]
        
        # In production, integrate with payment gateway (EcoCash, Paynow, etc.)
        # For now, simulate successful payment
        
        # Add tokens to user
        if package == 'UNLIMITED':
            tokens = 999999  # Unlimited (large number)
        else:
            tokens = float(package.replace('GB', ''))
        
        current_user.tokens += tokens
        
        # Record transaction
        transaction = Transaction(
            user_id=current_user.id,
            type='purchase',
            amount=price,
            tokens=tokens,
            description=f'Purchased {package} package'
        )
        db.session.add(transaction)
        
        # Add to your earnings
        admin_earnings = AdminEarnings.query.first()
        commission = price * (Config.YOUR_COMMISSION_PER_GB / Config.TOKEN_PRICE_PER_GB)
        admin_earnings.total_earnings += commission
        admin_earnings.total_transactions += 1
        admin_earnings.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Successfully purchased {package} package!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('connect.html', packages=Config.ZIMBABWE_TOKEN_PACKAGES)

@app.route('/api/session/<session_id>/usage', methods=['POST'])
@login_required
def update_usage(session_id):
    """API endpoint to update data usage"""
    session = SharingSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    data_used_mb = data.get('data_used_mb', 0)
    
    # Update session data usage
    session.data_used_mb += data_used_mb
    
    # Deduct tokens from user
    data_used_gb = data_used_mb / 1024
    if session.user_id:
        user = User.query.get(session.user_id)
        user.tokens -= data_used_gb
        
        # If user runs out of tokens, disconnect
        if user.tokens <= 0:
            session.is_active = False
            session.ended_at = datetime.utcnow()
    
    # Add earnings to sharer
    sharer = User.query.get(session.sharer_id)
    earnings = data_used_gb * Config.SHARER_EARNINGS_PER_GB
    sharer.earnings += earnings
    
    # Add to your earnings
    admin_earnings = AdminEarnings.query.first()
    your_earnings = data_used_gb * Config.YOUR_COMMISSION_PER_GB
    admin_earnings.total_earnings += your_earnings
    admin_earnings.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'data_used_gb': data_used_gb})

@app.route('/api/session/<session_id>/stop', methods=['POST'])
@login_required
def stop_session(session_id):
    """Stop sharing session"""
    session = SharingSession.query.filter_by(
        session_id=session_id,
        sharer_id=current_user.id
    ).first()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin')
@login_required
def admin():
    # In production, add proper admin authentication
    if current_user.email != 'admin@willssharestore.com':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    admin_earnings = AdminEarnings.query.first()
    total_users = User.query.count()
    total_sharers = User.query.filter_by(is_sharer=True).count()
    active_sessions = SharingSession.query.filter_by(is_active=True).count()
    
    recent_transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(20).all()
    
    return render_template('admin.html',
                         earnings=admin_earnings,
                         total_users=total_users,
                         total_sharers=total_sharers,
                         active_sessions=active_sessions,
                         transactions=recent_transactions)

if __name__ == '__main__':
    app.run(debug=True)
