import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class ScraperScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
        self.results_callback = None

    def set_results_callback(self, callback: Callable):
        self.results_callback = callback

    def add_scraping_job(
        self,
        job_id: str,
        scraper,
        urls: List[Dict],
        interval_minutes: int = 60
    ):
        async def job_function():
            try:
                logger.info(f"Starting scheduled scraping job: {job_id}")
                results = await scraper.scrape_multiple(urls)

                if self.results_callback:
                    await self.results_callback(job_id, results)

                logger.info(f"Completed scraping job: {job_id}, {len(results)} URLs processed")
            except Exception as e:
                logger.error(f"Error in scraping job {job_id}: {str(e)}")

        trigger = IntervalTrigger(minutes=interval_minutes)
        job = self.scheduler.add_job(
            job_function,
            trigger,
            id=job_id,
            name=f"Scraping job: {job_id}",
            replace_existing=True
        )
        self.jobs[job_id] = job

        logger.info(f"Scheduled scraping job {job_id} to run every {interval_minutes} minutes")

    def remove_job(self, job_id: str):
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed scraping job: {job_id}")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scraper scheduler started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scraper scheduler stopped")

    def get_job_status(self, job_id: str) -> Dict:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            return {
                'id': job_id,
                'next_run': job.next_run_time,
                'active': True
            }
        return {
            'id': job_id,
            'next_run': None,
            'active': False
        }

    def list_jobs(self) -> List[Dict]:
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]

    async def run_job_now(self, job_id: str):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            await job.func()
            logger.info(f"Manually triggered job: {job_id}")
        else:
            logger.warning(f"Job {job_id} not found")