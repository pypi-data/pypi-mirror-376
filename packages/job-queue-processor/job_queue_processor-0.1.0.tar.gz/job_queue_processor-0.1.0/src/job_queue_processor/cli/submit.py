#!/usr/bin/env python3
"""
Job Submission CLI - Submit jobs to the job queue.

This script allows you to:
- Submit single jobs with command and arguments
- Submit bulk jobs from a Python list
- Set custom timeouts for jobs
- Add custom metadata to jobs
"""

import argparse
import json
import sys
from typing import Dict, Any, List
from ..queue import JobQueue


def submit_single_job(queue: JobQueue,
                     command: str,
                     args: List[str],
                     timeout: int,
                     metadata: Dict[str, Any] = None) -> str:
    """Submit a single job to the queue."""
    job_id = queue.submit_job(command, args, timeout, metadata)
    print(f"📋 Job submitted successfully!")
    print(f"   Job ID: {job_id}")
    print(f"   Command: {command}")
    print(f"   Args: {args}")
    print(f"   Timeout: {timeout}s")
    if metadata:
        print(f"   Metadata: {metadata}")
    return job_id


def submit_bulk_jobs(queue: JobQueue, jobs_list: List[Dict[str, Any]]) -> List[str]:
    """Submit multiple jobs from a list."""
    print(f"📦 Submitting {len(jobs_list)} jobs...")

    job_ids = queue.submit_bulk_jobs(jobs_list)

    print(f"✅ All jobs submitted successfully!")
    print(f"   Total jobs: {len(job_ids)}")
    print(f"   Job IDs: {[jid[:8] + '...' for jid in job_ids[:3]]}" +
          (f" (+{len(job_ids)-3} more)" if len(job_ids) > 3 else ""))

    return job_ids


def main():
    """Main entry point for job submission."""
    parser = argparse.ArgumentParser(
        description="Submit jobs to the job queue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit a simple job
  job-submit script.py

  # Submit job with arguments and custom timeout
  job-submit script.py --args --query dogs --timeout 300

  # Submit job with multiple arguments
  job-submit script.py --args --input data.csv --output results.json

  # Submit job with metadata
  job-submit script.py --metadata '{"priority": 1, "team": "data"}'

  # Show queue statistics
  job-submit --stats
        """
    )

    # Main command argument
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to run (e.g., 'script.py' or 'python script.py')"
    )

    # Optional arguments
    parser.add_argument(
        "--args",
        nargs="*",
        default=[],
        help="Arguments to pass to the command"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Job timeout in seconds (default: 1800 = 30 minutes)"
    )

    parser.add_argument(
        "--metadata",
        type=str,
        help="Custom metadata as JSON string"
    )

    # Database configuration
    parser.add_argument(
        "--db-name",
        default="job_queue",
        help="MongoDB database name (default: job_queue)"
    )

    parser.add_argument(
        "--collection",
        default="jobs",
        help="MongoDB collection name (default: jobs)"
    )

    # Bulk submission
    parser.add_argument(
        "--bulk",
        metavar="JSON_STRING",
        help="Submit multiple jobs from JSON string"
    )

    # Statistics
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show queue statistics and exit"
    )

    args = parser.parse_args()

    # Initialize job queue
    try:
        queue = JobQueue(
            db_name=args.db_name,
            collection_name=args.collection
        )
    except Exception as e:
        print(f"❌ Failed to connect to job queue: {e}")
        print("💡 Make sure MongoDB is running and MONGODB_URI is set")
        return 1

    try:
        # Handle statistics request
        if args.stats:
            stats = queue.get_job_stats()
            print("📊 Job Queue Statistics:")
            print(f"   Pending: {stats['pending']}")
            print(f"   Running: {stats['running']}")
            print(f"   Completed: {stats['completed']}")
            print(f"   Failed: {stats['failed']}")
            return 0

        # Handle bulk submission
        if args.bulk:
            try:
                jobs_list = json.loads(args.bulk)
                if not isinstance(jobs_list, list):
                    raise ValueError("Bulk jobs must be a JSON array")

                submit_bulk_jobs(queue, jobs_list)
                return 0

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --bulk argument: {e}")
                return 1
            except Exception as e:
                print(f"❌ Error in bulk submission: {e}")
                return 1

        # Handle single job submission
        if not args.command:
            print("❌ Error: Command is required (or use --stats or --bulk)")
            parser.print_help()
            return 1

        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --metadata: {e}")
                return 1

        submit_single_job(queue, args.command, args.args, args.timeout, metadata)
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    finally:
        queue.close()


if __name__ == "__main__":
    sys.exit(main())