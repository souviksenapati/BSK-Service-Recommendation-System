"""
Admin endpoints for manual scheduler control and testing.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..scheduler.sync_scheduler import (
    trigger_sync_now,
    scheduler,
    _sync_in_progress
)

router = APIRouter()
logger = logging.getLogger(__name__)

SCHEDULER_LOCK_FILE = '/tmp/bsk_scheduler.lock'


class TriggerResponse(BaseModel):
    status: str
    message: str


@router.post("/trigger-sync", response_model=TriggerResponse)
async def manual_trigger_sync():
    """
    Manually trigger the sync job immediately (admin use).
    Returns immediately - sync runs in background thread.
    """
    try:
        logger.info("📞 Manual sync trigger requested via API")
        trigger_sync_now()
        return TriggerResponse(
            status="triggered",
            message="Manual sync job started in background. Check logs for progress."
        )
    except RuntimeError as e:
        # Sync already in progress
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status():
    """
    Get current scheduler status and upcoming jobs.
    Works correctly across all Gunicorn workers by checking the lock file.
    """
    try:
        # Check if scheduler is running on THIS worker
        local_running = scheduler.running
        
        # Check if scheduler is running on ANY worker (via lock file)
        overall_running = local_running
        scheduler_pid = os.getpid() if local_running else None
        
        if not local_running:
            # This request hit a non-scheduler worker — check lock file
            if os.path.exists(SCHEDULER_LOCK_FILE):
                try:
                    with open(SCHEDULER_LOCK_FILE, 'r') as f:
                        scheduler_pid = int(f.read().strip())
                    os.kill(scheduler_pid, 0)  # Check if process exists
                    overall_running = True
                except (ValueError, OSError, ProcessLookupError):
                    scheduler_pid = None
        
        # Get jobs (only available on the scheduler worker)
        jobs = []
        if local_running:
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return {
            "status": "running" if overall_running else "stopped",
            "sync_in_progress": _sync_in_progress,
            "scheduler_pid": scheduler_pid,
            "this_worker_is_scheduler": local_running,
            "scheduled_jobs": jobs,
            "job_count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
