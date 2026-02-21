"""Scheduled task scheduler using APScheduler."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.services.arxiv_crawler import crawl_all_subscriptions


# Global scheduler instance
_scheduler: BackgroundScheduler = None


def init_scheduler() -> BackgroundScheduler:
    """Initialize and start the background task scheduler."""
    global _scheduler

    if _scheduler is None:
        _scheduler = BackgroundScheduler()

        # arXiv crawl job - runs every 6 hours
        _scheduler.add_job(
            crawl_all_subscriptions,
            IntervalTrigger(hours=6),
            id="arxiv_crawl_all",
            name="Crawl arXiv for all active subscriptions",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
        )

        # Alternative: Run at specific times (e.g., 2am, 8am, 2pm, 8pm)
        # _scheduler.add_job(
        #     crawl_all_subscriptions,
        #     CronTrigger(hour="2,8,14,20", minute=0),
        #     id="arxiv_crawl_all",
        #     name="Crawl arXiv for all active subscriptions",
        #     replace_existing=True,
        # )

        _scheduler.start()
        print("[Scheduler] Started with jobs:", _scheduler.get_jobs())

    return _scheduler


def get_scheduler() -> BackgroundScheduler:
    """Get the scheduler instance."""
    return _scheduler


def shutdown_scheduler():
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
