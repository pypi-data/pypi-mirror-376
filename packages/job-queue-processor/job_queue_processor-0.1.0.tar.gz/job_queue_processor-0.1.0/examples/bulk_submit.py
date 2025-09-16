#!/usr/bin/env python3
"""
Example: Bulk job submission using the Python API.

This demonstrates how to programmatically submit multiple jobs.
"""

import os
from job_queue_processor import JobQueue


def submit_bulk_processing_jobs():
    """Submit multiple data processing jobs."""

    # Initialize queue
    queue = JobQueue()

    print("📦 Submitting bulk processing jobs...")

    # Example: Process multiple data files
    jobs = []
    for i in range(5):
        jobs.append({
            "command": "examples/job_with_args.py",
            "args": [
                "--input", f"data_{i}.csv",
                "--output", f"result_{i}.json",
                "--operation", "analyze"
            ],
            "timeout": 300,  # 5 minutes
            "metadata": {
                "batch_id": "data_processing_001",
                "priority": 1,
                "team": "analytics"
            }
        })

    # Submit all jobs
    job_ids = queue.submit_bulk_jobs(jobs)

    print(f"✅ Submitted {len(job_ids)} jobs")
    print("Job IDs:", [jid[:8] + "..." for jid in job_ids])

    # Show queue stats
    stats = queue.get_job_stats()
    print(f"📊 Queue stats: {stats}")

    queue.close()

    return job_ids


def submit_mixed_jobs():
    """Submit jobs of different types with different configurations."""

    queue = JobQueue(
        db_name="my_project_jobs",  # Custom database name
        collection_name="tasks"     # Custom collection name
    )

    print("🔀 Submitting mixed job types...")

    # Different types of jobs
    jobs = [
        {
            "command": "examples/basic_job.py",
            "timeout": 60,
            "metadata": {"type": "basic", "priority": 3}
        },
        {
            "command": "python",
            "args": ["-c", "print('Hello from Python job'); import time; time.sleep(2)"],
            "timeout": 30,
            "metadata": {"type": "inline", "priority": 1}
        },
        {
            "command": "examples/job_with_args.py",
            "args": ["--input", "test.txt", "--output", "out.txt"],
            "timeout": 120,
            "metadata": {"type": "file_processing", "priority": 2}
        }
    ]

    job_ids = queue.submit_bulk_jobs(jobs)

    print(f"✅ Submitted {len(job_ids)} mixed jobs")

    queue.close()

    return job_ids


if __name__ == "__main__":
    print("🚀 Bulk job submission examples")
    print()

    # Example 1: Bulk processing
    submit_bulk_processing_jobs()
    print()

    # Example 2: Mixed job types
    submit_mixed_jobs()

    print()
    print("💡 To process these jobs, run:")
    print("   job-process --workers 3")
    print()
    print("💡 To monitor progress, run:")
    print("   job-monitor")