import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from config import Config
from database import db, DatabaseManager
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db_manager = DatabaseManager(app)

# Simple mock sentiment analyzer for demo
class MockSentimentAnalyzer:
    def analyze_text(self, text):
        sentiments = ['positive', 'negative', 'neutral']
        return {
            'text': text[:500],
            'sentiment': random.choice(sentiments),
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

        positive_count = sum(1 for s in sentiments if s['sentiment'] == 'positive')
        negative_count = sum(1 for s in sentiments if s['sentiment'] == 'negative')
        neutral_count = sum(1 for s in sentiments if s['sentiment'] == 'neutral')

        scores = [s['score'] for s in sentiments if 'score' in s]
        confidences = [s['confidence'] for s in sentiments if 'confidence' in s]

        average_score = sum(scores) / len(scores) if scores else 0.0
        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            'overall_sentiment': 'positive' if average_score > 0.2 else 'negative' if average_score < -0.2 else 'neutral',
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'average_score': round(average_score, 3),
            'average_confidence': round(average_confidence, 3),
            'total_analyzed': len(sentiments)
        }

sentiment_analyzer = MockSentimentAnalyzer()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    try:
        # Generate mock data for demo
        stats = {
            'sentiment_distribution': {
                'positive': random.randint(20, 50),
                'negative': random.randint(10, 30),
                'neutral': random.randint(15, 40)
            },
            'average_score': random.uniform(-0.5, 0.5),
            'average_confidence': random.uniform(0.7, 0.95)
        }

        trends = {
            'direction': random.choice(['improving', 'declining', 'stable']),
            'change_rate': random.uniform(-20, 20)
        }

        return jsonify({
            'success': True,
            'stats': stats,
            'recent_count': random.randint(10, 100),
            'trends': trends,
            'last_updated': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sentiments/recent')
def get_recent_sentiments():
    try:
        # Generate mock sentiments for demo
        sentiments = []
        for i in range(20):
            sentiments.append({
                'id': i + 1,
                'text_snippet': f"Sample text snippet {i + 1}: This is a demo text for sentiment analysis...",
                'sentiment': random.choice(['positive', 'negative', 'neutral']),
                'score': random.uniform(-1, 1),
                'confidence': random.uniform(0.7, 1),
                'analyzed_at': (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat(),
                'source_name': random.choice(['News Site', 'Social Media', 'Blog', 'Forum'])
            })

        return jsonify({
            'success': True,
            'data': sentiments,
            'count': len(sentiments)
        })
    except Exception as e:
        logger.error(f"Error getting recent sentiments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/aggregated/<period_type>')
def get_aggregated_data(period_type):
    try:
        days = request.args.get('days', 7, type=int)

        # Generate mock aggregated data
        data = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            data.append({
                'period': date.isoformat(),
                'total_items': random.randint(50, 200),
                'sentiment_distribution': {
                    'positive': random.randint(20, 80),
                    'negative': random.randint(10, 50),
                    'neutral': random.randint(20, 70)
                },
                'average_score': random.uniform(-0.5, 0.5),
                'average_confidence': random.uniform(0.7, 0.95)
            })

        return jsonify({
            'success': True,
            'data': data,
            'period_type': period_type,
            'days': days
        })
    except Exception as e:
        logger.error(f"Error getting aggregated data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        # Mock scraping result
        result = {
            'url': url,
            'texts': [f"Scraped content from {url}"],
            'success': True,
            'sentiment_analysis': sentiment_analyzer.get_aggregate_sentiment([
                sentiment_analyzer.analyze_text(f"Sample text from {url}")
            ])
        }

        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error scraping URL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sources')
def get_sources():
    return jsonify({
        'success': True,
        'sources': ['News Site', 'Social Media', 'Blog', 'Forum']
    })

@app.route('/api/export/<format>')
def export_data(format):
    try:
        # Mock export
        if format == 'json':
            return jsonify({
                'success': True,
                'data': [],
                'exported_at': datetime.utcnow().isoformat()
            })
        elif format == 'csv':
            from flask import Response
            return Response(
                "id,sentiment,score,confidence\n1,positive,0.8,0.95\n",
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=sentiment_data.csv'}
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs')
def get_scraping_jobs():
    return jsonify({
        'success': True,
        'active_jobs': [],
        'configured_jobs': []
    })

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)