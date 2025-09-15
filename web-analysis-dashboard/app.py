import os
import asyncio
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from config import Config
from database import db, DatabaseManager
from scraper import WebScraper, ScraperScheduler
from analyzer import SentimentAnalyzer, DataAggregator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db_manager = DatabaseManager(app)
sentiment_analyzer = None
data_aggregator = DataAggregator()
scraper_scheduler = ScraperScheduler()

def init_sentiment_analyzer():
    global sentiment_analyzer
    try:
        sentiment_analyzer = SentimentAnalyzer()
        logger.info("Sentiment analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
        sentiment_analyzer = None

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
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

@app.route('/api/sentiments/recent')
def get_recent_sentiments():
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
def get_aggregated_data(period_type):
    try:
        days = request.args.get('days', 7, type=int)
        source = request.args.get('source')

        data = db_manager.get_aggregated_data(
            period_type=period_type,
            days=days,
            source_name=source
        )

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
async def scrape_url():
    try:
        data = request.json
        url = data.get('url')
        selector = data.get('selector')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        scraper = WebScraper({'use_playwright': True})
        result = await scraper.scrape(url, selector)

        if result['success']:
            scraped = db_manager.save_scraped_data(result)

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

@app.route('/api/sources')
def get_sources():
    try:
        sources = db_manager.get_sources()
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        logger.error(f"Error getting sources: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/<format>')
def export_data(format):
    try:
        days = request.args.get('days', 7, type=int)
        source = request.args.get('source')

        sentiments = db_manager.get_recent_sentiments(hours=days*24, source_name=source)

        if format == 'json':
            return jsonify({
                'success': True,
                'data': sentiments,
                'exported_at': datetime.utcnow().isoformat()
            })
        elif format == 'csv':
            import pandas as pd
            import io

            df = pd.DataFrame(sentiments)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            from flask import Response
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=sentiment_data.csv'}
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid format'}), 400
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs')
def get_scraping_jobs():
    try:
        jobs = scraper_scheduler.list_jobs()
        db_jobs = db_manager.get_scraping_jobs()

        return jsonify({
            'success': True,
            'active_jobs': jobs,
            'configured_jobs': db_jobs
        })
    except Exception as e:
        logger.error(f"Error getting scraping jobs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/trigger/<job_id>', methods=['POST'])
async def trigger_job(job_id):
    try:
        await scraper_scheduler.run_job_now(job_id)
        return jsonify({
            'success': True,
            'message': f'Job {job_id} triggered successfully'
        })
    except Exception as e:
        logger.error(f"Error triggering job: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

async def process_scraping_results(job_id: str, results: list):
    logger.info(f"Processing {len(results)} results from job {job_id}")

    for result in results:
        if result['success']:
            scraped = db_manager.save_scraped_data(result)

            if sentiment_analyzer and result.get('texts'):
                sentiments = sentiment_analyzer.analyze_batch(result['texts'])
                db_manager.save_sentiment_results(scraped.id, sentiments)

    db_manager.update_job_run_time(job_id)

def setup_scheduled_jobs():
    scraper_scheduler.set_results_callback(process_scraping_results)

    for website in Config.WEBSITES_TO_SCRAPE:
        if website.get('enabled'):
            job_id = f"scrape_{website['name'].replace(' ', '_').lower()}"
            scraper = WebScraper({'use_playwright': True})

            scraper_scheduler.add_scraping_job(
                job_id=job_id,
                scraper=scraper,
                urls=[website],
                interval_minutes=Config.SCRAPING_INTERVAL_MINUTES
            )

    scraper_scheduler.start()

if __name__ == '__main__':
    init_sentiment_analyzer()
    setup_scheduled_jobs()

    app.run(debug=True, host='0.0.0.0', port=5000)