import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, or_, func
from .models import db, ScrapedData, SentimentResult, AggregatedData, ScrapingJob

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, app=None):
        self.db = db
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.db.init_app(app)
        with app.app_context():
            self.db.create_all()

    def save_scraped_data(self, data: Dict) -> ScrapedData:
        try:
            scraped = ScrapedData(
                url=data.get('url'),
                source_name=data.get('source_name'),
                title=data.get('metadata', {}).get('title'),
                content=' '.join(data.get('texts', [])),
                meta=data.get('metadata'),
                scraped_at=data.get('scraped_at', datetime.utcnow()),
                success=data.get('success', True),
                error_message=data.get('error')
            )
            self.db.session.add(scraped)
            self.db.session.commit()
            return scraped
        except Exception as e:
            logger.error(f"Error saving scraped data: {str(e)}")
            self.db.session.rollback()
            raise

    def save_sentiment_results(self, scraped_id: int, sentiments: List[Dict]) -> List[SentimentResult]:
        try:
            results = []
            for sentiment in sentiments:
                result = SentimentResult(
                    scraped_data_id=scraped_id,
                    text_snippet=sentiment.get('text'),
                    sentiment=sentiment.get('sentiment'),
                    score=sentiment.get('score'),
                    confidence=sentiment.get('confidence'),
                    analyzed_at=sentiment.get('analyzed_at', datetime.utcnow())
                )
                self.db.session.add(result)
                results.append(result)

            self.db.session.commit()
            return results
        except Exception as e:
            logger.error(f"Error saving sentiment results: {str(e)}")
            self.db.session.rollback()
            raise

    def save_aggregated_data(self, aggregation: Dict) -> AggregatedData:
        try:
            agg_data = AggregatedData(
                period_type=aggregation.get('period_type'),
                period_start=aggregation.get('period_start'),
                period_end=aggregation.get('period_end'),
                source_name=aggregation.get('source_name'),
                total_items=aggregation.get('total_items'),
                positive_count=aggregation.get('sentiment_distribution', {}).get('positive', 0),
                negative_count=aggregation.get('sentiment_distribution', {}).get('negative', 0),
                neutral_count=aggregation.get('sentiment_distribution', {}).get('neutral', 0),
                average_score=aggregation.get('average_score'),
                average_confidence=aggregation.get('average_confidence')
            )
            self.db.session.add(agg_data)
            self.db.session.commit()
            return agg_data
        except Exception as e:
            logger.error(f"Error saving aggregated data: {str(e)}")
            self.db.session.rollback()
            raise

    def get_recent_sentiments(
        self,
        hours: int = 24,
        source_name: Optional[str] = None
    ) -> List[Dict]:
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = self.db.session.query(SentimentResult).join(ScrapedData)

            query = query.filter(SentimentResult.analyzed_at >= since)

            if source_name:
                query = query.filter(ScrapedData.source_name == source_name)

            results = query.order_by(SentimentResult.analyzed_at.desc()).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            logger.error(f"Error getting recent sentiments: {str(e)}")
            return []

    def get_aggregated_data(
        self,
        period_type: str = 'daily',
        days: int = 7,
        source_name: Optional[str] = None
    ) -> List[Dict]:
        try:
            since = datetime.utcnow() - timedelta(days=days)
            query = self.db.session.query(AggregatedData)

            query = query.filter(
                and_(
                    AggregatedData.period_type == period_type,
                    AggregatedData.period_start >= since
                )
            )

            if source_name:
                query = query.filter(AggregatedData.source_name == source_name)

            results = query.order_by(AggregatedData.period_start).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            logger.error(f"Error getting aggregated data: {str(e)}")
            return []

    def get_sentiment_stats(self, days: int = 30) -> Dict:
        try:
            since = datetime.utcnow() - timedelta(days=days)

            stats = self.db.session.query(
                func.count(SentimentResult.id).label('total'),
                func.avg(SentimentResult.score).label('avg_score'),
                func.avg(SentimentResult.confidence).label('avg_confidence'),
                SentimentResult.sentiment,
                func.count(SentimentResult.sentiment).label('sentiment_count')
            ).filter(
                SentimentResult.analyzed_at >= since
            ).group_by(SentimentResult.sentiment).all()

            total = sum(s.sentiment_count for s in stats)
            sentiments = {s.sentiment: s.sentiment_count for s in stats}

            return {
                'total_analyzed': total,
                'average_score': round(stats[0].avg_score, 3) if stats and stats[0].avg_score else 0,
                'average_confidence': round(stats[0].avg_confidence, 3) if stats and stats[0].avg_confidence else 0,
                'sentiment_distribution': {
                    'positive': sentiments.get('positive', 0),
                    'negative': sentiments.get('negative', 0),
                    'neutral': sentiments.get('neutral', 0)
                },
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting sentiment stats: {str(e)}")
            return {}

    def get_sources(self) -> List[str]:
        try:
            sources = self.db.session.query(
                ScrapedData.source_name
            ).distinct().filter(
                ScrapedData.source_name.isnot(None)
            ).all()
            return [s[0] for s in sources]
        except Exception as e:
            logger.error(f"Error getting sources: {str(e)}")
            return []

    def cleanup_old_data(self, days: int = 30):
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            self.db.session.query(SentimentResult).filter(
                SentimentResult.analyzed_at < cutoff
            ).delete()

            self.db.session.query(ScrapedData).filter(
                ScrapedData.scraped_at < cutoff
            ).delete()

            self.db.session.query(AggregatedData).filter(
                AggregatedData.created_at < cutoff
            ).delete()

            self.db.session.commit()
            logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            self.db.session.rollback()

    def get_scraping_jobs(self, active_only: bool = True) -> List[Dict]:
        try:
            query = self.db.session.query(ScrapingJob)
            if active_only:
                query = query.filter(ScrapingJob.is_active == True)
            jobs = query.all()
            return [j.to_dict() for j in jobs]
        except Exception as e:
            logger.error(f"Error getting scraping jobs: {str(e)}")
            return []

    def update_job_run_time(self, job_name: str):
        try:
            job = self.db.session.query(ScrapingJob).filter_by(job_name=job_name).first()
            if job:
                job.last_run = datetime.utcnow()
                job.next_run = datetime.utcnow() + timedelta(minutes=job.interval_minutes)
                self.db.session.commit()
        except Exception as e:
            logger.error(f"Error updating job run time: {str(e)}")
            self.db.session.rollback()
