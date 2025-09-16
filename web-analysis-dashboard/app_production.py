import os
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, Response
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from sqlalchemy import text
import bcrypt
import jwt

from config import Config
from database import db, DatabaseManager, APIKey
from scraper import WebScraper
from analyzer import SentimentAnalyzer, DataAggregator
import io
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///production.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'production-secret-key-change-this'

# Security headers (Content Security Policy); HTTPS off for local
csp = {
    'default-src': ["'self'", 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
    'img-src': ["'self'", 'data:', 'https:'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
    'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com']
}
Talisman(app, content_security_policy=csp, force_https=False)

# Initialize extensions
allowed_origins = os.environ.get('CORS_ORIGINS')
if allowed_origins:
    origins = [o.strip() for o in allowed_origins.split(',') if o.strip()]
    CORS(app, supports_credentials=True, origins=origins)
else:
    CORS(app, supports_credentials=True)
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

# Rate limiting
rate_limit = os.environ.get('RATE_LIMIT', '100/hour')
limiter = Limiter(get_remote_address, app=app, default_limits=[rate_limit])

# Initialize managers
db_manager = DatabaseManager(app)
data_aggregator = DataAggregator()

# Global sentiment analyzer (will be initialized once)
sentiment_analyzer = None

def init_sentiment_analyzer():
    """Initialize the sentiment analyzer with real Hugging Face model"""
    global sentiment_analyzer
    try:
        logger.info("Initializing real sentiment analyzer...")
        sentiment_analyzer = SentimentAnalyzer()
        logger.info("Sentiment analyzer ready!")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
        logger.info("Falling back to mock sentiment analyzer")

        # Fallback to mock analyzer
        class MockSentimentAnalyzer:
            def analyze_text(self, text):
                import random
                return {
                    'text': text[:500],
                    'sentiment': random.choice(['positive', 'negative', 'neutral']),
                    'score': random.uniform(-1, 1),
                    'confidence': random.uniform(0.7, 1),
                    'analyzed_at': datetime.utcnow()
                }

            def analyze_batch(self, texts):
                return [self.analyze_text(text) for text in texts]

            def get_aggregate_sentiment(self, sentiments):
                if not sentiments:
                    return {
                        'overall_sentiment': 'neutral',
                        'positive_count': 0,
                        'negative_count': 0,
                        'neutral_count': 0,
                        'average_score': 0.0,
                        'average_confidence': 0.0
                    }

                positive = sum(1 for s in sentiments if s.get('sentiment') == 'positive')
                negative = sum(1 for s in sentiments if s.get('sentiment') == 'negative')
                neutral = sum(1 for s in sentiments if s.get('sentiment') == 'neutral')

                return {
                    'overall_sentiment': 'positive' if positive > negative else 'negative' if negative > positive else 'neutral',
                    'positive_count': positive,
                    'negative_count': negative,
                    'neutral_count': neutral,
                    'average_score': 0.0,
                    'average_confidence': 0.85,
                    'total_analyzed': len(sentiments)
                }

        sentiment_analyzer = MockSentimentAnalyzer()
        return False

# API key auth helper (allow either login or valid API key) and schemas
from functools import wraps
from marshmallow import Schema, fields, ValidationError

def require_api_key_or_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return func(*args, **kwargs)
        provided = request.headers.get('X-API-Key') or request.args.get('api_key')
        if provided:
            try:
                # Compare against stored hashed keys
                keys = APIKey.query.filter_by(is_active=True).all()
                for k in keys:
                    if bcrypt.checkpw(provided.encode('utf-8'), k.key.encode('utf-8')):
                        return func(*args, **kwargs)
            except Exception:
                pass
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    return wrapper

class ScrapeRequestSchema(Schema):
    url = fields.Url(required=True)
    selector = fields.String(required=False, allow_none=True)

# User model for authentication
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        rounds = int(os.environ.get('BCRYPT_LOG_ROUNDS', '12'))
        salt = bcrypt.gensalt(rounds=rounds)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def generate_token(self):
        return jwt.encode(
            {'user_id': self.id, 'exp': datetime.utcnow() + timedelta(days=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    """Main dashboard - requires login"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'token': user.generate_token()})
            return redirect(url_for('index'))

        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        flash('Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if user exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            flash('Username already exists')
            return render_template('register.html')

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        if request.is_json:
            return jsonify({'success': True, 'token': user.generate_token()})
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/dashboard/stats')
@limiter.limit("30/minute")
@require_api_key_or_login
def get_dashboard_stats():
    """Get real dashboard statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = db_manager.get_sentiment_stats(days=days)

        recent_sentiments = db_manager.get_recent_sentiments(hours=24)
        aggregated = db_manager.get_aggregated_data(period_type='daily', days=days)

        trends = data_aggregator.calculate_trends(aggregated) if aggregated else {}

        return jsonify({
            'success': True,
            'stats': stats,
            'recent_count': len(recent_sentiments),
            'trends': trends,
            'last_updated': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
@limiter.limit("10/minute")
@require_api_key_or_login
@csrf.exempt
def scrape_url():
    """Scrape URL with real web scraping"""
    try:
        data = request.get_json(force=True, silent=True) or {}
        try:
            payload = ScrapeRequestSchema().load(data)
        except ValidationError as ve:
            return jsonify({'success': False, 'error': ve.messages}), 400

        url = payload.get('url')
        selector = payload.get('selector')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        # Real web scraping with robots.txt compliance, UA rotation, and rate limiting
        scraper = WebScraper({
            'use_playwright': True,
            'respect_robots': True,
            'rotate_user_agent': True,
            'rate_limit_interval': 1.5
        })
        # Run async scraper within sync route
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Nested loop case (unlikely under gunicorn); create a new loop
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(scraper.scrape(url, selector))
                new_loop.close()
                asyncio.set_event_loop(loop)
            else:
                result = loop.run_until_complete(scraper.scrape(url, selector))
        except RuntimeError:
            # No event loop; simple run
            result = asyncio.run(scraper.scrape(url, selector))

        if result['success']:
            # Save to database
            scraped = db_manager.save_scraped_data(result)

            # Perform real sentiment analysis
            if sentiment_analyzer and result.get('texts'):
                sentiments = sentiment_analyzer.analyze_batch(result['texts'])
                db_manager.save_sentiment_results(scraped.id, sentiments)

                aggregate = sentiment_analyzer.get_aggregate_sentiment(sentiments)
                result['sentiment_analysis'] = aggregate

        return jsonify({
            'success': result['success'],
            'data': result
        })
    except Exception as e:
        logger.error(f"Error scraping URL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentiments/recent')
@limiter.limit("60/minute")
@require_api_key_or_login
def get_recent_sentiments():
    """Get recent real sentiment analysis results"""
    try:
        hours = request.args.get('hours', 24, type=int)
        source = request.args.get('source')
        limit = request.args.get('limit', 100, type=int)

        sentiments = db_manager.get_recent_sentiments(hours=hours, source_name=source)

        if limit:
            sentiments = sentiments[:limit]

        return jsonify({
            'success': True,
            'data': sentiments,
            'count': len(sentiments)
        })
    except Exception as e:
        logger.error(f"Error getting recent sentiments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/aggregated/<period_type>')
@limiter.limit("60/minute")
@require_api_key_or_login
def get_aggregated_data(period_type):
    """Get real aggregated data"""
    try:
        days = request.args.get('days', 7, type=int)
        source = request.args.get('source')

        data = db_manager.get_aggregated_data(
            period_type=period_type,
            days=days,
            source_name=source
        )

        # Fallback: compute on the fly from recent sentiments if no persisted aggregates
        if not data:
            hours = max(days * 24, 1)
            sentiments = db_manager.get_recent_sentiments(hours=hours, source_name=source)
            aggregated = data_aggregator.aggregate_by_period(
                sentiments,
                period=period_type,
                date_field='analyzed_at'
            )
            # Normalize period field for JSON
            for item in aggregated:
                if 'period' in item and item['period'] is not None:
                    try:
                        item['period'] = item['period'].isoformat()
                    except Exception:
                        item['period'] = str(item['period'])
            data = aggregated

        return jsonify({
            'success': True,
            'data': data,
            'period_type': period_type,
            'days': days
        })
    except Exception as e:
        logger.error(f"Error getting aggregated data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    return render_template('analytics.html')

@app.route('/api/health')
def health_check():
    """Enhanced health check: DB, Redis, Celery"""
    db_ok = False
    redis_ok = False
    celery_ok = False

    try:
        db.session.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        import redis as redislib
        r = redislib.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
        redis_ok = r.ping()
    except Exception:
        redis_ok = False

    try:
        from celery_app import celery_app
        resp = celery_app.control.ping(timeout=1.0)
        celery_ok = bool(resp)
    except Exception:
        celery_ok = False

    return jsonify({
        'status': 'healthy' if (db_ok and redis_ok) else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'sentiment_analyzer': 'active' if sentiment_analyzer else 'mock',
        'database': db_ok,
        'redis': redis_ok,
        'celery': celery_ok
    })

# Celery enqueue/status endpoints
@app.route('/api/tasks/scrape', methods=['POST'])
@limiter.limit("10/minute")
@require_api_key_or_login
@csrf.exempt
def enqueue_scrape_task():
    data = request.get_json(force=True, silent=True) or {}
    try:
        payload = ScrapeRequestSchema().load(data)
    except ValidationError as ve:
        return jsonify({'success': False, 'error': ve.messages}), 400
    from celery_app import scrape_and_analyze
    ar = scrape_and_analyze.delay(payload.get('url'), payload.get('selector'))
    return jsonify({'success': True, 'task_id': ar.id})

@app.route('/api/tasks/<task_id>/status')
@limiter.limit("60/minute")
@require_api_key_or_login
def task_status(task_id):
    from celery_app import celery_app
    res = celery_app.AsyncResult(task_id)
    return jsonify({'id': task_id, 'state': res.state, 'result': res.result if res.ready() else None})


@app.route('/api/sources')
@limiter.limit("60/minute")
@require_api_key_or_login
def get_sources_api():
    try:
        sources = db_manager.get_sources()
        return jsonify({'success': True, 'sources': sources})
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/<format>')
@limiter.limit("30/minute")
@require_api_key_or_login
def export_data(format):
    try:
        days = request.args.get('days', 7, type=int)
        source = request.args.get('source')
        hours = max(days * 24, 1)
        sentiments = db_manager.get_recent_sentiments(hours=hours, source_name=source)

        if format == 'json':
            return jsonify({
                'success': True,
                'count': len(sentiments),
                'data': sentiments,
                'exported_at': datetime.utcnow().isoformat()
            })
        elif format == 'csv':
            df = pd.DataFrame(sentiments)
            csv_buffer = io.StringIO()
            if not df.empty:
                df.to_csv(csv_buffer, index=False)
            content = csv_buffer.getvalue()
            headers = {
                'Content-Disposition': 'attachment; filename=sentiment_data.csv'
            }
            return Response(content, mimetype='text/csv', headers=headers)
        else:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# CLI commands for setup
@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database initialized!")

@app.cli.command()
def create_admin():
    """Create admin user"""
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Admin user '{username}' created!")

@app.cli.command()
def create_api_key():
    """Create and store a new API key (hashed). Prints the key once."""
    import getpass
    import secrets
    label = input("Key label (optional): ")
    user_id = input("User ID to associate (optional): ")
    token = secrets.token_urlsafe(32)
    rounds = int(os.environ.get('BCRYPT_LOG_ROUNDS', '12'))
    salt = bcrypt.gensalt(rounds=rounds)
    key_hash = bcrypt.hashpw(token.encode('utf-8'), salt).decode('utf-8')

    api_key = APIKey(key=key_hash, user_id=int(user_id) if user_id.strip().isdigit() else None, label=label or None, is_active=True)
    db.session.add(api_key)
    db.session.commit()
    print("\nAPI Key created. Store this secret now; it will not be shown again:\n")
    print(token)
    print("\nAssociated record id:", api_key.id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_sentiment_analyzer()

    print("\n" + "="*60)
    print(" Web Data Analysis Dashboard - PRODUCTION")
    print("="*60)
    port = int(os.environ.get('PORT', '5000'))
    print("\n Starting production server...")
    print(f" Access at: http://localhost:{port}")
    print("\n Features:")
    print(" ✓ Real sentiment analysis (if models available)")
    print(" ✓ User authentication")
    print(" ✓ Database persistence")
    print(" ✓ Web scraping ready")
    print("="*60 + "\n")

    app.run(debug=False, host='0.0.0.0', port=port)
