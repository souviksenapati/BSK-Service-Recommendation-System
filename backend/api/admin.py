"""
Admin endpoints for manual scheduler control and testing.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..scheduler.sync_scheduler import (
    trigger_sync_now,
    scheduler
)

router = APIRouter()
logger = logging.getLogger(__name__)


class TriggerResponse(BaseModel):
    status: str
    message: str


@router.post("/trigger-sync", response_model=TriggerResponse)
async def manual_trigger_sync():
    """
    Manually trigger the sync job immediately (admin use).
    """
    try:
        logger.info("📞 Manual sync trigger requested via API")
        trigger_sync_now()
        return TriggerResponse(
            status="triggered",
            message="Manual sync job started. Check logs for progress."
        )
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status():
    """
    Get current scheduler status and upcoming jobs.
    """
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running" if scheduler.running else "stopped",
            "scheduled_jobs": jobs,
            "job_count": len(jobs)
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
