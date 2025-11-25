"""
Main entry point for the FastF1 worker service.
"""
import asyncio
import signal
import sys

from .config import settings
from .database import close_db, init_db
from .ingestion import ingestion_service
from .logger import logger
from .scheduler import worker_scheduler


class WorkerService:
    """Main worker service."""
    
    def __init__(self):
        """Initialize worker service."""
        self.logger = logger.bind(component="worker")
        self.running = False
    
    async def start(self):
        """Start the worker service."""
        try:
            self.logger.info(
                "Starting FastF1 worker service",
                worker_name=settings.WORKER_NAME
            )
            
            # Initialize database
            await init_db()
            
            # Start scheduler
            worker_scheduler.start()
            
            self.running = True
            self.logger.info("Worker service started successfully")
            
            # Keep the service running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(
                "Worker service error",
                error=str(e)
            )
            raise
    
    async def stop(self):
        """Stop the worker service."""
        self.logger.info("Stopping worker service")
        self.running = False
        
        # Shutdown scheduler
        worker_scheduler.shutdown()
        
        # Close database
        await close_db()
        
        self.logger.info("Worker service stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(
            "Received shutdown signal",
            signal=signal.Signals(signum).name
        )
        asyncio.create_task(self.stop())


async def main():
    """Main function."""
    worker = WorkerService()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, worker.handle_signal)
    signal.signal(signal.SIGTERM, worker.handle_signal)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker service interrupted")
        sys.exit(0)
