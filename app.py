from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, SharingSession, Transaction, AdminEarnings
from config import Config
import os
from datetime import datetime
import logging

app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Initialize admin earnings if not exists
        if not AdminEarnings.query.first():
            admin_earnings = AdminEarnings()
            db.session.add(admin_earnings)
            db.session.commit()
            logger.info("Admin earnings initialized")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html', 
                         supported_countries=Config.SUPPORTED_COUNTRIES,
                         packages=Config.ZIMBABWE_TOKEN_PACKAGES,
                         config=Config)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        country = request.form.get('country')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('index'))
        
        user = User(email=email, country=country, phone=phone)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user)
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
    flash('Invalid email or password', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        return render_template('coming_soon.html', 
                             country=current_user.country,
                             message=Config.COMING_SOON_MESSAGE)
    
    try:
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
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/share')
@login_required
def share():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        flash('Service not available in your country yet', 'error')
        return redirect(url_for('dashboard'))
    
    try:
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"Share error: {e}")
        flash('Error creating sharing session', 'error')
        return redirect(url_for('dashboard'))

@app.route('/connect', methods=['GET', 'POST'])
@login_required
def connect():
    if current_user.country not in Config.SUPPORTED_COUNTRIES:
        flash('Service not available in your country yet', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        connection_token = request.form.get('connection_token')
        
        try:
            session = SharingSession.query.filter_by(
                connection_token=connection_token,
                is_active=True
            ).first()
            
            if not session:
                flash('Invalid connection code', 'error')
                return redirect(url_for('connect'))
            
            if current_user.tokens <= 0:
                flash('Insufficient tokens. Please purchase tokens first.', 'error')
                return redirect(url_for('connect'))
            
            # Connect user to session
            session.user_id = current_user.id
            db.session.commit()
            
            flash('Connected successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Connect error: {e}")
            flash('Error connecting to hotspot', 'error')
            return redirect(url_for('connect'))
    
    # GET request - show available sessions
    try:
        available_sessions = SharingSession.query.filter_by(
            is_active=True,
            user_id=None
        ).limit(10).all()
        
        return render_template('connect.html', 
                             sessions=available_sessions,
                             packages=Config.ZIMBABWE_TOKEN_PACKAGES,
                             user_tokens=current_user.tokens)
    except Exception as e:
        logger.error(f"Connect page error: {e}")
        flash('Error loading connection page', 'error')
        return redirect(url_for('dashboard'))

@app.route('/buy-tokens', methods=['POST'])
@login_required
def buy_tokens():
    package = request.form.get('package')
    
    if package not in Config.ZIMBABWE_TOKEN_PACKAGES:
        flash('Invalid package', 'error')
        return redirect(url_for('connect'))
    
    try:
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
        commission = price * 0.5  # 50% commission for now
        admin_earnings.total_earnings += commission
        admin_earnings.total_transactions += 1
        admin_earnings.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Successfully purchased {package} package!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Buy tokens error: {e}")
        flash('Error processing purchase', 'error')
        return redirect(url_for('connect'))

@app.route('/api/session/<session_id>/usage', methods=['POST'])
@login_required
def update_usage(session_id):
    """API endpoint to update data usage"""
    try:
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update usage error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/stop', methods=['POST'])
@login_required
def stop_session(session_id):
    """Stop sharing session"""
    try:
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"Stop session error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
@login_required
def admin():
    # In production, add proper admin authentication
    if current_user.email != 'admin@willssharestore.com':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
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
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'error')
        return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
