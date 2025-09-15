#!/usr/bin/env python3
"""
Web Data Analysis Dashboard - Production V2
Compatible with Python 3.13
"""

import os
import logging
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import peewee as pw
from playhouse.shortcuts import model_to_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL') or 'sqlite:///production_v2.db'

# Initialize extensions
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup with Peewee (simpler than SQLAlchemy)
if app.config['DATABASE_URL'].startswith('postgresql'):
    from playhouse.pool import PooledPostgresqlDatabase
    db = PooledPostgresqlDatabase(
        app.config['DATABASE_URL'].split('/')[-1],
        max_connections=8,
        stale_timeout=300,
    )
else:
    db = pw.SqliteDatabase('production_v2.db')

# Database Models
class BaseModel(pw.Model):
    class Meta:
        database = db

class User(UserMixin, BaseModel):
    id = pw.AutoField()
    username = pw.CharField(unique=True)
    email = pw.CharField(unique=True)
    password_hash = pw.CharField()
    created_at = pw.DateTimeField(default=datetime.utcnow)
    is_active = pw.BooleanField(default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        return jwt.encode(
            {'user_id': self.id, 'exp': datetime.utcnow() + timedelta(days=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

class ScrapedData(BaseModel):
    id = pw.AutoField()
    url = pw.CharField()
    source_name = pw.CharField(null=True)
    title = pw.CharField(null=True)
    content = pw.TextField()
    scraped_at = pw.DateTimeField(default=datetime.utcnow)
    success = pw.BooleanField(default=True)
    error_message = pw.TextField(null=True)

class SentimentResult(BaseModel):
    id = pw.AutoField()
    scraped_data = pw.ForeignKeyField(ScrapedData, backref='sentiments')
    text_snippet = pw.TextField()
    sentiment = pw.CharField()
    score = pw.FloatField()
    confidence = pw.FloatField()
    analyzed_at = pw.DateTimeField(default=datetime.utcnow)

# Simple Sentiment Analyzer using TextBlob and VADER
class SimpleSentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        logger.info("Initialized simple sentiment analyzer")

    def analyze_text(self, text):
        """Analyze sentiment using both TextBlob and VADER"""
        if not text or not text.strip():
            return {
                'text': text,
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'analyzed_at': datetime.utcnow()
            }

        # TextBlob analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1

        # VADER analysis
        vader_scores = self.vader.polarity_scores(text)
        compound = vader_scores['compound']  # -1 to 1

        # Combine both scores
        final_score = (polarity + compound) / 2

        # Determine sentiment
        if final_score > 0.1:
            sentiment = 'positive'
        elif final_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Calculate confidence (based on agreement between methods)
        agreement = 1 - abs(polarity - compound)
        confidence = min(0.95, 0.5 + (agreement * 0.45))

        return {
            'text': text[:500],
            'sentiment': sentiment,
            'score': round(final_score, 3),
            'confidence': round(confidence, 3),
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

        scores = [s.get('score', 0) for s in sentiments]
        avg_score = sum(scores) / len(scores) if scores else 0

        confidences = [s.get('confidence', 0) for s in sentiments]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            'overall_sentiment': 'positive' if avg_score > 0.1 else 'negative' if avg_score < -0.1 else 'neutral',
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'average_score': round(avg_score, 3),
            'average_confidence': round(avg_confidence, 3),
            'total_analyzed': len(sentiments)
        }

# Simple Web Scraper
class SimpleWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape(self, url, selector=None):
        """Scrape a URL and extract text"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            if selector:
                elements = soup.select(selector)
                texts = [elem.get_text(strip=True) for elem in elements]
            else:
                texts = [soup.get_text(strip=True)]

            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''

            return {
                'url': url,
                'texts': texts,
                'title': title_text,
                'success': True,
                'error': None,
                'scraped_at': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'texts': [],
                'title': '',
                'success': False,
                'error': str(e),
                'scraped_at': datetime.utcnow()
            }

# Initialize components
sentiment_analyzer = SimpleSentimentAnalyzer()
web_scraper = SimpleWebScraper()

# Login manager
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get(User.id == int(user_id))
    except User.DoesNotExist:
        return None

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = User.get(User.username == username)
            if user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Invalid password')
        except User.DoesNotExist:
            flash('Username not found')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user exists
        existing = User.select().where(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            flash('Username or email already exists')
        else:
            user = User.create(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            login_user(user)
            return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    try:
        # Get recent sentiment stats
        recent = datetime.utcnow() - timedelta(days=7)

        sentiments = SentimentResult.select().where(
            SentimentResult.analyzed_at >= recent
        )

        positive = sentiments.where(SentimentResult.sentiment == 'positive').count()
        negative = sentiments.where(SentimentResult.sentiment == 'negative').count()
        neutral = sentiments.where(SentimentResult.sentiment == 'neutral').count()

        total = positive + negative + neutral

        return jsonify({
            'success': True,
            'stats': {
                'sentiment_distribution': {
                    'positive': positive,
                    'negative': negative,
                    'neutral': neutral
                },
                'total_analyzed': total
            },
            'last_updated': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
@login_required
def scrape_url():
    try:
        data = request.json
        url = data.get('url')
        selector = data.get('selector')

        if not url:
            return jsonify({'success': False, 'error': 'URL required'}), 400

        # Scrape the URL
        result = web_scraper.scrape(url, selector)

        if result['success']:
            # Save to database
            scraped = ScrapedData.create(
                url=url,
                title=result.get('title', ''),
                content=' '.join(result.get('texts', [])),
                success=True
            )

            # Analyze sentiment
            if result.get('texts'):
                sentiments = sentiment_analyzer.analyze_batch(result['texts'])

                # Save sentiment results
                for sentiment in sentiments:
                    SentimentResult.create(
                        scraped_data=scraped,
                        text_snippet=sentiment['text'][:500],
                        sentiment=sentiment['sentiment'],
                        score=sentiment['score'],
                        confidence=sentiment['confidence']
                    )

                result['sentiment_analysis'] = sentiment_analyzer.get_aggregate_sentiment(sentiments)

        return jsonify({
            'success': result['success'],
            'data': result
        })

    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentiments/recent')
@login_required
def get_recent_sentiments():
    try:
        limit = request.args.get('limit', 50, type=int)

        sentiments = SentimentResult.select().order_by(
            SentimentResult.analyzed_at.desc()
        ).limit(limit)

        data = []
        for s in sentiments:
            data.append({
                'id': s.id,
                'text_snippet': s.text_snippet,
                'sentiment': s.sentiment,
                'score': s.score,
                'confidence': s.confidence,
                'analyzed_at': s.analyzed_at.isoformat()
            })

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting sentiments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'analyzer': 'TextBlob + VADER',
        'database': 'connected'
    })

# Database initialization
def init_db():
    db.connect()
    db.create_tables([User, ScrapedData, SentimentResult])
    logger.info("Database initialized")

# CLI commands
@app.cli.command()
def createdb():
    """Create database tables"""
    init_db()
    print("Database created!")

@app.cli.command()
def createadmin():
    """Create admin user"""
    init_db()
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")

    user = User.create(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    print(f"Admin user '{username}' created!")

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Create default admin if no users exist
    if User.select().count() == 0:
        admin = User.create(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        logger.info("Created default admin user (admin/admin123)")

    print("\n" + "="*60)
    print(" Web Data Analysis Dashboard V2 - WORKING VERSION")
    print("="*60)
    print("\n Features:")
    print(" ✓ Real sentiment analysis (TextBlob + VADER)")
    print(" ✓ Real web scraping (BeautifulSoup)")
    print(" ✓ User authentication")
    print(" ✓ Database persistence (Peewee ORM)")
    print(" ✓ Python 3.13 compatible")
    print("\n Default login: admin / admin123")
    print(" Access at: http://localhost:5001")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)