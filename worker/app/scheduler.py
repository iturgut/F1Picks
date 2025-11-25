"""
Scheduler for periodic FastF1 data polling.
"""
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from .config import settings
from .database import Event, EventStatus, get_db_session
from .ingestion import ingestion_service
from .logger import logger


class WorkerScheduler:
    """Scheduler for FastF1 worker tasks."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.logger = logger.bind(component="scheduler")
    
    async def poll_completed_events(self):
        """
        Poll for completed events that need results ingestion.
        
        This runs periodically to check for events that have ended
        and attempt to fetch their results from FastF1.
        """
        try:
            self.logger.info("Polling for completed events")
            
            async for session in get_db_session():
                # Find completed events without results
                query = select(Event).where(
                    Event.status == EventStatus.COMPLETED,
                    Event.end_time <= datetime.utcnow()
                ).order_by(Event.end_time.desc()).limit(20)
                
                result = await session.execute(query)
                events = result.scalars().all()
                
                self.logger.info(
                    "Found completed events to process",
                    events_count=len(events)
                )
                
                # Process each event
                for event in events:
                    self.logger.info(
                        "Attempting to ingest results",
                        event_id=str(event.id),
                        event_name=event.name
                    )
                    
                    success = await ingestion_service.poll_for_session_data(event.id)
                    
                    if success:
                        self.logger.info(
                            "Successfully ingested results",
                            event_id=str(event.id)
                        )
                    else:
                        self.logger.debug(
                            "Results not yet available",
                            event_id=str(event.id)
                        )
                    
                    # Add small delay between requests to avoid rate limiting
                    await asyncio.sleep(2)
                
        except Exception as e:
            self.logger.error(
                "Error polling completed events",
                error=str(e)
            )
    
    async def update_event_statuses(self):
        """
        Update event statuses based on current time.
        
        Transitions events from SCHEDULED -> LIVE -> COMPLETED
        based on their start and end times.
        """
        try:
            self.logger.info("Updating event statuses")
            
            now = datetime.utcnow()
            
            async for session in get_db_session():
                # Update scheduled events that have started
                query = select(Event).where(
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time <= now,
                    Event.end_time > now
                )
                result = await session.execute(query)
                events_to_live = result.scalars().all()
                
                for event in events_to_live:
                    event.status = EventStatus.LIVE
                    self.logger.info(
                        "Event status updated to LIVE",
                        event_id=str(event.id),
                        event_name=event.name
                    )
                
                # Update live events that have ended
                query = select(Event).where(
                    Event.status == EventStatus.LIVE,
                    Event.end_time <= now
                )
                result = await session.execute(query)
                events_to_completed = result.scalars().all()
                
                for event in events_to_completed:
                    event.status = EventStatus.COMPLETED
                    self.logger.info(
                        "Event status updated to COMPLETED",
                        event_id=str(event.id),
                        event_name=event.name
                    )
                
                await session.commit()
                
                self.logger.info(
                    "Event status update complete",
                    live_count=len(events_to_live),
                    completed_count=len(events_to_completed)
                )
                
        except Exception as e:
            self.logger.error(
                "Error updating event statuses",
                error=str(e)
            )
    
    def start(self):
        """Start the scheduler."""
        if not settings.ENABLE_SCHEDULER:
            self.logger.info("Scheduler disabled by configuration")
            return
        
        # Schedule periodic tasks
        self.scheduler.add_job(
            self.update_event_statuses,
            trigger=IntervalTrigger(minutes=5),
            id="update_event_statuses",
            name="Update event statuses",
            replace_existing=True,
        )
        
        self.scheduler.add_job(
            self.poll_completed_events,
            trigger=IntervalTrigger(minutes=settings.POLL_INTERVAL_MINUTES),
            id="poll_completed_events",
            name="Poll for completed event results",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self.logger.info(
            "Scheduler started",
            poll_interval=settings.POLL_INTERVAL_MINUTES
        )
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler shutdown")


# Global scheduler instance
worker_scheduler = WorkerScheduler()
