import os
import asyncio
from celery import Celery


def make_celery() -> Celery:
    broker_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("REDIS_URL", broker_url)

    celery = Celery(
        "web_analysis",
        broker=broker_url,
        backend=result_backend,
        include=["web-analysis-dashboard.celery_app"],
    )

    celery.conf.update(
        task_default_queue="default",
        task_time_limit=600,
        task_soft_time_limit=540,
    )
    return celery


celery_app = make_celery()


@celery_app.task(name="ping")
def ping():
    return "ok"


@celery_app.task(name="scrape_and_analyze")
def scrape_and_analyze(url: str, selector: str | None = None) -> dict:
    """Scaffold task: scrape a URL and (optionally) analyze sentiments.
    Uses the existing app context, DB manager, and scraper.
    """
    from app_production import app
    from database import DatabaseManager
    from scraper import WebScraper
    from analyzer import SentimentAnalyzer

    with app.app_context():
        dbm = DatabaseManager(app)
        scraper = WebScraper({
            "use_playwright": False,
            "respect_robots": True,
            "rotate_user_agent": True,
            "rate_limit_interval": 1.5,
        })

        try:
            # WebScraper.scrape is async; run it in this worker
            result = asyncio.run(scraper.scrape(url, selector))
        except RuntimeError:
            # If an event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(scraper.scrape(url, selector))
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

        if not result.get("success"):
            return {"success": False, "error": result.get("error"), "url": url}

        scraped = dbm.save_scraped_data(result)

        sentiments = []
        if result.get("texts"):
            try:
                analyzer = SentimentAnalyzer()
                sentiments = analyzer.analyze_batch(result["texts"])[:100]
                dbm.save_sentiment_results(scraped.id, sentiments)
            except Exception:
                # Sentiment analysis is optional in scaffold; ignore failures
                pass

        return {
            "success": True,
            "scraped_id": scraped.id,
            "sentiments_saved": len(sentiments),
        }

