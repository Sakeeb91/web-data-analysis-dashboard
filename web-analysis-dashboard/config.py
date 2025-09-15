import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///data_analysis.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SCRAPING_INTERVAL_MINUTES = 60

    WEBSITES_TO_SCRAPE = [
        {
            'name': 'Example News Site',
            'url': 'https://example.com/news',
            'selector': 'article.content',
            'enabled': True
        }
    ]

    SENTIMENT_BATCH_SIZE = 32

    AGGREGATION_PERIODS = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1)
    }

    MAX_RETRIES = 3
    RETRY_DELAY = 5

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'