"""
Automated Sync Scheduler
Handles weekly data synchronization and static file regeneration.
"""

import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import nest_asyncio
import threading

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

from ..database.connection import SessionLocal
from ..api.sync import SyncRequest, sync_data as sync_endpoint
from ..api.generate import regenerate_files, RegenerationType

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Scheduler configuration from environment
SCHEDULER_TIMEZONE = os.getenv('SCHEDULER_TIMEZONE', 'Asia/Kolkata')
SYNC_DAY_OF_WEEK = os.getenv('SYNC_DAY_OF_WEEK', 'sun')
SYNC_HOUR = int(os.getenv('SYNC_HOUR', '0'))
SYNC_MINUTE = int(os.getenv('SYNC_MINUTE', '0'))
STATIC_REGEN_DELAY_HOURS = int(os.getenv('STATIC_REGEN_DELAY_HOURS', '1'))

# Initialize APScheduler with configured timezone
scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)

# Tables to sync from external BSK API (in order of dependency)
# These map to database tables: ml_bsk_master, ml_district, ml_provision, ml_citizen_master, services
TABLES_TO_SYNC = [
    'bsk_master',           # → ml_bsk_master (BSK centers)
    'district',             # → ml_district (Districts)  
    'service_master',       # → services (Service catalog)
    'provision',            # → ml_provision (Historical transactions)
    'citizen_master'        # → ml_citizen_master (Citizen data)
]

# Thread-safe sync guard to prevent concurrent syncs (within same worker process)
_sync_lock = threading.Lock()
_sync_in_progress = False


def sync_all_tables():
    """
    Sync all tables from external API.
    Runs every Sunday at 12:00 AM.
    Continues even if one table fails.
    Thread-safe: prevents concurrent syncs via _sync_lock.
    """
    global _sync_in_progress
    
    # Prevent concurrent sync runs (scheduler + manual trigger)
    if not _sync_lock.acquire(blocking=False):
        logger.warning("⚠️ Sync already in progress - skipping this trigger")
        return
    
    _sync_in_progress = True
    logger.info("="*70)
    logger.info("🔄 WEEKLY SYNC JOB STARTED")
    logger.info(f"⏰ Time: {datetime.now()}")
    logger.info("="*70)
    
    db: Session = SessionLocal()
    results = []
    
    try:
        for table in TABLES_TO_SYNC:
            logger.info(f"\n📊 Syncing table: {table}")
            try:
                # Create sync request
                request = SyncRequest(
                    target_table=table,
                    start_date=None,  # Use last sync date from metadata
                    force_full=False
                )
                
                # Call sync endpoint function directly (not HTTP)
                # Use synchronous database operations to avoid async issues
                import asyncio
                try:
                    # Try to get existing loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is already running, use run_in_executor
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            # Wait indefinitely for sync to complete (no timeout)
                            future = pool.submit(asyncio.run, sync_endpoint(request, db))
                            result = future.result()  # Blocks until completion
                    else:
                        result = loop.run_until_complete(sync_endpoint(request, db))
                except RuntimeError:
                    # No event loop in current thread, create one
                    result = asyncio.run(sync_endpoint(request, db))
                except Exception as async_error:
                    # Catch ANY async-related errors and continue
                    logger.error(f"❌ Async error for {table}: {str(async_error)[:200]}")
                    raise  # Re-raise to be caught by outer except
                
                results.append({
                    'table': table,
                    'status': 'success',
                    'records': result.get('total_records_processed', 0),
                    'timestamp': datetime.now()
                })
                
                logger.info(f"✅ {table}: SUCCESS - {result.get('total_records_processed', 0)} records")
                
            except Exception as e:
                # Log error but continue with other tables
                error_msg = str(e)
                results.append({
                    'table': table,
                    'status': 'failed',
                    'error': error_msg,
                    'timestamp': datetime.now()
                })
                
                logger.error(f"❌ {table}: FAILED - {error_msg}")
                continue
        
        # Log summary
        logger.info("\n" + "="*70)
        logger.info("📈 SYNC JOB SUMMARY")
        logger.info("-"*70)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        
        logger.info(f"✅ Successful: {success_count}/{len(TABLES_TO_SYNC)}")
        logger.info(f"❌ Failed: {failed_count}/{len(TABLES_TO_SYNC)}")
        
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            if result['status'] == 'success':
                logger.info(f"{status_icon} {result['table']}: {result['records']} records")
            else:
                logger.info(f"{status_icon} {result['table']}: {result['error'][:50]}")
        
        logger.info("="*70)
        
        # Schedule static file generation after configured delay
        if success_count > 0:  # Only if at least one table synced successfully
            from datetime import timedelta
            from pytz import timezone as pytz_timezone
            
            # Use timezone-aware datetime
            tz = pytz_timezone(SCHEDULER_TIMEZONE)
            run_time = datetime.now(tz) + timedelta(hours=STATIC_REGEN_DELAY_HOURS)
            
            logger.info(f"\n⏱️  Scheduling static file regeneration at {run_time} (in {STATIC_REGEN_DELAY_HOURS} hour(s))")
            
            scheduler.add_job(
                regenerate_static_files,
                trigger=DateTrigger(run_date=run_time),
                id='one_time_static_generation',
                replace_existing=True,
                max_instances=1,  # Only one instance at a time
                coalesce=True  # Don't queue duplicates
            )
        else:
            logger.warning("⚠️  No tables synced successfully, skipping static file generation")
    
    finally:
        db.close()
        _sync_in_progress = False
        _sync_lock.release()
        logger.info("🔓 Sync lock released")


def regenerate_static_files():
    """
    Regenerate all static files.
    Runs 1 hour after sync completion.
    """
    logger.info("="*70)
    logger.info("🔧 STATIC FILE REGENERATION STARTED")
    logger.info(f"⏰ Time: {datetime.now()}")
    logger.info("="*70)
    
    db: Session = SessionLocal()
    
    try:
        # Call new regenerate endpoint with type="all"
        import asyncio
        import concurrent.futures
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        regenerate_files(RegenerationType.ALL, db)
                    ).result()
            else:
                result = loop.run_until_complete(regenerate_files(RegenerationType.ALL, db))
        except RuntimeError:
            result = asyncio.run(regenerate_files(RegenerationType.ALL, db))
        
        logger.info("\n📊 Generated Files:")
        if result.get('district_files'):
            logger.info(f"  ✅ District: {', '.join(result['district_files'])}")
        if result.get('block_files'):
            logger.info(f"  ✅ Block: {', '.join(result['block_files'])}")
        if result.get('demographic_files'):
            logger.info(f"  ✅ Demographic: {', '.join(result['demographic_files'])}")
        
        logger.info("\n✅ Static file regeneration completed successfully")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Static file regeneration failed: {e}")
        logger.error("="*70)
    
    finally:
        db.close()


def start_scheduler():
    """
    Start the scheduler with all configured jobs.
    Called on application startup.
    
    BULLETPROOF IMPLEMENTATION:
    - Uses file-based lock to ensure ONLY ONE scheduler runs across all workers
    - Detects and cleans up stale locks from crashed processes
    - No timeouts - waits indefinitely for jobs to complete
    - Graceful shutdown handling
    """
    import fcntl
    import atexit
    import signal
    
    lock_file_path = '/tmp/bsk_scheduler.lock'
    lock_file_handle = None
    
    def cleanup_lock():
        """Clean up lock file on exit"""
        try:
            if lock_file_handle:
                fcntl.flock(lock_file_handle.fileno(), fcntl.LOCK_UN)
                lock_file_handle.close()
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
        except Exception as e:
            logger.warning(f"Lock cleanup warning: {e}")
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("🛑 Shutdown signal received - cleaning up scheduler...")
        cleanup_lock()
        shutdown_scheduler()
        
    try:
        # Try to acquire exclusive lock (non-blocking)
        # CRITICAL: Use os.open with O_CREAT | O_RDWR to create without truncating.
        # open('w') would truncate the file, causing a race condition where
        # a later worker truncates the PID written by the lock-winning worker.
        fd = os.open(lock_file_path, os.O_CREAT | os.O_RDWR, 0o644)
        lock_file_handle = os.fdopen(fd, 'r+')
        fcntl.flock(lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # We won the lock — now safely write our PID
        lock_file_handle.seek(0)
        lock_file_handle.truncate()
        lock_file_handle.write(str(os.getpid()))
        lock_file_handle.flush()
        
        # Register cleanup handlers
        atexit.register(cleanup_lock)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("="*70)
        logger.info("🚀 INITIALIZING SYNC SCHEDULER (Primary Instance)")
        logger.info(f"   PID: {os.getpid()} | Lock: {lock_file_path}")
        logger.info("="*70)
        
    except (IOError, OSError) as e:
        # Another process holds the lock
        try:
            # Check if lock is stale (process crashed)
            with open(lock_file_path, 'r') as f:
                locked_pid = int(f.read().strip())
            
            # Check if that process is still running
            try:
                os.kill(locked_pid, 0)  # Signal 0 just checks if process exists
                # Process exists - scheduler already running
                logger.info(f"⏭️  Scheduler already running (PID: {locked_pid}) - skipping this worker")
                return
            except OSError:
                # Process doesn't exist - stale lock, clean it up
                logger.warning(f"⚠️  Stale lock detected (PID: {locked_pid}) - cleaning up and retrying")
                try:
                    os.remove(lock_file_path)
                    # Retry acquiring lock
                    return start_scheduler()
                except Exception as cleanup_error:
                    logger.error(f"❌ Failed to clean stale lock: {cleanup_error}")
                    return
        except Exception as check_error:
            logger.info(f"⏭️  Scheduler locked by another worker - skipping")
            return
    
    # Add weekly sync job with configuration from environment
    logger.info(f"⏰ Schedule: {SYNC_DAY_OF_WEEK.upper()} at {SYNC_HOUR:02d}:{SYNC_MINUTE:02d} ({SCHEDULER_TIMEZONE})")
    
    scheduler.add_job(
        sync_all_tables,
        trigger=CronTrigger(
            day_of_week=SYNC_DAY_OF_WEEK,
            hour=SYNC_HOUR,
            minute=SYNC_MINUTE,
            timezone=SCHEDULER_TIMEZONE
        ),
        id='weekly_sync',
        name=f'Weekly Data Sync ({SYNC_DAY_OF_WEEK.upper()} {SYNC_HOUR:02d}:{SYNC_MINUTE:02d})',
        replace_existing=True,
        max_instances=1,  # Only one instance can run at a time
        coalesce=True,  # If missed, run once (don't queue multiple)
        misfire_grace_time=3600  # Allow 1 hour grace for missed jobs
    )
    
    # Start the scheduler
    scheduler.start()
    
    logger.info("✅ Scheduler started successfully")
    logger.info("\n📅 Scheduled Jobs:")
    
    for job in scheduler.get_jobs():
        logger.info(f"  • {job.name}")
        logger.info(f"    ID: {job.id}")
        logger.info(f"    Trigger: {job.trigger}")
        logger.info(f"    Next run: {job.next_run_time}")
    
    logger.info("="*70)


def shutdown_scheduler():
    """
    Gracefully shutdown the scheduler.
    Called on application shutdown.
    """
    logger.info("🛑 Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("✅ Scheduler shutdown complete")


# Manual trigger functions for testing/admin use
def trigger_sync_now():
    """Manually trigger sync job immediately (runs in background thread)"""
    if _sync_in_progress:
        raise RuntimeError("Sync job is already running. Check logs for progress.")
    
    logger.info("🔧 Manual sync trigger requested - starting background sync")
    thread = threading.Thread(target=sync_all_tables, name="manual-sync", daemon=True)
    thread.start()
