"""
Scheduler — runs the newsletter pipeline on a daily schedule.
Supports cron-like scheduling with retry logic.
"""

import time
import signal
import logging
import schedule as schedule_lib
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


class Scheduler:
    """Manages daily scheduled execution of the newsletter pipeline."""

    def __init__(self, config: dict):
        self.config = config
        sched_config = config.get("schedule", {})
        self.send_time = sched_config.get("time", "08:00")
        self.timezone = sched_config.get("timezone", "Asia/Kolkata")
        self.retry_attempts = sched_config.get("retry_attempts", 3)
        self.retry_delay = sched_config.get("retry_delay_minutes", 15)
        self._running = True

    def start(self, job_func: Callable):
        """Start the scheduler with a daily job."""
        logger.info(f"⏰ Scheduling daily newsletter at {self.send_time} ({self.timezone})")

        # Schedule the job
        schedule_lib.every().day.at(self.send_time).do(self._run_with_retry, job_func)

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        logger.info(f"✅ Scheduler started. Next run: {schedule_lib.next_run()}")
        logger.info("   Press Ctrl+C to stop.\n")

        while self._running:
            schedule_lib.run_pending()
            time.sleep(30)  # Check every 30 seconds

        logger.info("Scheduler stopped.")

    def _run_with_retry(self, job_func: Callable):
        """Run the job with retry logic."""
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"🚀 Running newsletter pipeline (attempt {attempt}/{self.retry_attempts})")
                logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}\n")

                job_func()

                logger.info(f"\n✅ Pipeline completed successfully!")
                return

            except Exception as e:
                logger.error(f"❌ Pipeline failed on attempt {attempt}: {e}")

                if attempt < self.retry_attempts:
                    logger.info(f"⏳ Retrying in {self.retry_delay} minutes...")
                    time.sleep(self.retry_delay * 60)
                else:
                    logger.error(f"💀 All {self.retry_attempts} attempts failed. Will retry tomorrow.")

    def _shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info("\n\n🛑 Shutdown signal received. Stopping scheduler...")
        self._running = False

    def run_once(self, job_func: Callable):
        """Run the pipeline once immediately (for testing)."""
        self._run_with_retry(job_func)
