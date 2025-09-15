from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ScrapedData(db.Model):
    __tablename__ = 'scraped_data'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(100))
    title = db.Column(db.String(500))
    content = db.Column(db.Text)
    metadata = db.Column(db.JSON)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    sentiments = db.relationship('SentimentResult', backref='scraped_data', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'source_name': self.source_name,
            'title': self.title,
            'content': self.content[:500] if self.content else None,
            'metadata': self.metadata,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'success': self.success,
            'error_message': self.error_message
        }

class SentimentResult(db.Model):
    __tablename__ = 'sentiment_results'

    id = db.Column(db.Integer, primary_key=True)
    scraped_data_id = db.Column(db.Integer, db.ForeignKey('scraped_data.id'))
    text_snippet = db.Column(db.Text)
    sentiment = db.Column(db.String(20))
    score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'scraped_data_id': self.scraped_data_id,
            'text_snippet': self.text_snippet[:200] if self.text_snippet else None,
            'sentiment': self.sentiment,
            'score': self.score,
            'confidence': self.confidence,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }

class AggregatedData(db.Model):
    __tablename__ = 'aggregated_data'

    id = db.Column(db.Integer, primary_key=True)
    period_type = db.Column(db.String(20))
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    source_name = db.Column(db.String(100))
    total_items = db.Column(db.Integer)
    positive_count = db.Column(db.Integer)
    negative_count = db.Column(db.Integer)
    neutral_count = db.Column(db.Integer)
    average_score = db.Column(db.Float)
    average_confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'source_name': self.source_name,
            'total_items': self.total_items,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count,
            'neutral_count': self.neutral_count,
            'average_score': self.average_score,
            'average_confidence': self.average_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScrapingJob(db.Model):
    __tablename__ = 'scraping_jobs'

    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), unique=True)
    url_pattern = db.Column(db.String(500))
    selector = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    interval_minutes = db.Column(db.Integer, default=60)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'job_name': self.job_name,
            'url_pattern': self.url_pattern,
            'selector': self.selector,
            'is_active': self.is_active,
            'interval_minutes': self.interval_minutes,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }