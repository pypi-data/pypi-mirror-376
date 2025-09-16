#!/usr/bin/env python3
"""
Generic Job Queue implementation using MongoDB.

This module provides a flexible job queue system with the following features:
- Submit jobs with commands and arguments
- Get next pending job (FIFO order)
- Mark jobs as completed or failed based on exit codes
- Simple status tracking: pending → running → completed/failed
- Configurable database and collection names
- Support for custom job metadata
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class JobQueue:
    """Generic job queue using MongoDB as backend."""

    def __init__(self,
                 mongo_uri: Optional[str] = None,
                 db_name: str = "job_queue",
                 collection_name: str = "jobs"):
        """
        Initialize connection to MongoDB.

        Args:
            mongo_uri: MongoDB connection URI (defaults to MONGODB_URI env var)
            db_name: Database name (default: "job_queue")
            collection_name: Collection name (default: "jobs")
        """
        if mongo_uri is None:
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.jobs = self.db[collection_name]

        # Create indexes for better performance
        self.jobs.create_index("status")
        self.jobs.create_index("created_at")

    def submit_job(self,
                   command: str,
                   args: Optional[List[str]] = None,
                   timeout: int = 1800,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a job to the queue.

        Args:
            command: Command to execute (e.g., "script.py" or "my_module.main")
            args: List of command line arguments
            timeout: Job timeout in seconds (default: 30 minutes)
            metadata: Additional custom fields for the job

        Returns:
            str: Job ID
        """
        job = {
            "job_id": str(uuid.uuid4()),
            "command": command,
            "args": args or [],
            "timeout": timeout,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "attempts": 0,
            "result": None,
            "stdout": None,
            "stderr": None,
            "exit_code": None,
            "error": None
        }

        # Add custom metadata if provided
        if metadata:
            job.update(metadata)

        self.jobs.insert_one(job)
        print(f"✅ Submitted job: {job['job_id']}")
        return job["job_id"]

    def submit_bulk_jobs(self, jobs_list: List[Dict[str, Any]]) -> List[str]:
        """
        Submit multiple jobs from a list.

        Args:
            jobs_list: List of job dictionaries with 'command', and optionally
                      'args', 'timeout', 'metadata'

        Returns:
            list: List of job IDs
        """
        job_ids = []
        for job_spec in jobs_list:
            job_id = self.submit_job(
                command=job_spec["command"],
                args=job_spec.get("args", []),
                timeout=job_spec.get("timeout", 1800),
                metadata=job_spec.get("metadata")
            )
            job_ids.append(job_id)

        print(f"✅ Submitted {len(job_ids)} jobs in bulk")
        return job_ids

    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Get next pending job and mark it as running.

        This operation is atomic - only one worker can claim a job.

        Returns:
            dict: Job document or None if no pending jobs
        """
        job = self.jobs.find_one_and_update(
            {"status": "pending"},
            {
                "$set": {
                    "status": "running",
                    "started_at": datetime.now(timezone.utc)
                },
                "$inc": {"attempts": 1}
            },
            sort=[("created_at", 1)],  # FIFO order
            return_document=True
        )

        if job:
            print(f"📋 Claimed job: {job['job_id'][:8]} - {job['command']}")

        return job

    def complete_job(self,
                     job_id: str,
                     stdout: str,
                     stderr: str,
                     exit_code: int) -> None:
        """
        Mark job as completed or failed based on exit code.

        Args:
            job_id: Job ID
            stdout: Standard output from process
            stderr: Standard error from process
            exit_code: Process exit code (0 = success, non-zero = failure)
        """
        status = "completed" if exit_code == 0 else "failed"

        update_data = {
            "status": status,
            "completed_at": datetime.now(timezone.utc),
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }

        # Add error message if failed
        if exit_code != 0:
            update_data["error"] = f"Process exited with code {exit_code}"
            if stderr.strip():
                update_data["error"] += f": {stderr.strip()}"

        self.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )

        status_emoji = "✅" if exit_code == 0 else "❌"
        print(f"{status_emoji} Job {job_id[:8]} {status}")

    def fail_job(self, job_id: str, error_message: str) -> None:
        """
        Mark job as failed with custom error message.

        Args:
            job_id: Job ID
            error_message: Error description
        """
        self.jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc),
                    "error": error_message
                }
            }
        )
        print(f"❌ Job {job_id[:8]} failed: {error_message}")

    def get_job_stats(self) -> Dict[str, int]:
        """Get basic statistics about jobs in the queue."""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]

        stats = {}
        for result in self.jobs.aggregate(pipeline):
            stats[result["_id"]] = result["count"]

        return {
            "pending": stats.get("pending", 0),
            "running": stats.get("running", 0),
            "completed": stats.get("completed", 0),
            "failed": stats.get("failed", 0)
        }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID."""
        return self.jobs.find_one({"job_id": job_id})

    def get_jobs_by_status(self,
                          status: str,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get jobs by status.

        Args:
            status: Job status to filter by
            limit: Maximum number of jobs to return

        Returns:
            List of job documents
        """
        cursor = self.jobs.find({"status": status}).sort("created_at", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def close(self) -> None:
        """Close MongoDB connection."""
        self.client.close()


if __name__ == "__main__":
    # Simple test
    queue = JobQueue()
    print("Queue stats:", queue.get_job_stats())