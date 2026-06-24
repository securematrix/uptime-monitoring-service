import asyncio
import logging
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import get_db_session
from models import Monitor
from monitor import check_monitor

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_jobs = {}

def sync_monitor_jobs():
    db = get_db_session()
    try:
        monitors = db.query(Monitor).filter(Monitor.is_paused == False).all()
        active_ids = []
        for monitor in monitors:
            job_id = f"monitor_{monitor.id}"
            active_ids.append(job_id)
            
            if job_id not in _jobs:
                logger.info(f"Scheduling monitor {monitor.name} every {monitor.frequency}s")
                job = scheduler.add_job(
                    check_monitor,
                    IntervalTrigger(seconds=monitor.frequency),
                    args=[monitor.id],
                    id=job_id,
                    replace_existing=True
                )
                _jobs[job_id] = job
            else:
                job = scheduler.get_job(job_id)
                if job and job.trigger.interval.total_seconds() != monitor.frequency:
                     scheduler.reschedule_job(job_id, trigger=IntervalTrigger(seconds=monitor.frequency))
                     logger.info(f"Rescheduled monitor {monitor.name} to {monitor.frequency}s")

        for job_id in list(_jobs.keys()):
            if job_id not in active_ids:
                logger.info(f"Removing scheduled job {job_id}")
                scheduler.remove_job(job_id)
                del _jobs[job_id]
                
    finally:
        db.close()

def start_scheduler():
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scheduler.start()
        
        scheduler.add_job(sync_monitor_jobs, IntervalTrigger(seconds=10), id="sync_jobs")
        loop.call_soon(sync_monitor_jobs)
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
