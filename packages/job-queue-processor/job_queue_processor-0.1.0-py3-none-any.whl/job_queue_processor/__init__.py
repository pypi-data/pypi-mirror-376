"""
Job Queue Processor

A simple, extensible job queue processor with MongoDB backend.

Example usage:
    from job_queue_processor import JobQueue, JobProcessor

    # Submit a job
    queue = JobQueue()
    job_id = queue.submit_job("script.py", args=["--input", "data.csv"])

    # Process jobs
    processor = JobProcessor(workers=3)
    processor.run()
"""

from .queue import JobQueue
from .processor import JobProcessor

__version__ = "0.1.0"
__all__ = ["JobQueue", "JobProcessor"]