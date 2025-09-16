#!/usr/bin/env python3
"""
Job Queue Monitor CLI - Simple monitoring tool for the job queue.

Shows current queue statistics and recent job activity.
"""

import time
import argparse
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..queue import JobQueue


def clear_screen():
    """Clear terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def format_duration(start_time, end_time=None):
    """Format duration between timestamps."""
    if not start_time:
        return "N/A"

    end = end_time or datetime.now(timezone.utc)
    delta = end - start_time

    if delta.total_seconds() < 60:
        return f"{int(delta.total_seconds())}s"
    elif delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() / 60)}m {int(delta.total_seconds() % 60)}s"
    else:
        hours = int(delta.total_seconds() / 3600)
        minutes = int((delta.total_seconds() % 3600) / 60)
        return f"{hours}h {minutes}m"


def show_queue_status(queue: JobQueue):
    """Display current queue status."""
    stats = queue.get_job_stats()

    print("📊 Job Queue Status")
    print("=" * 40)
    print(f"   Pending:   {stats['pending']:4d}")
    print(f"   Running:   {stats['running']:4d}")
    print(f"   Completed: {stats['completed']:4d}")
    print(f"   Failed:    {stats['failed']:4d}")
    print(f"   Total:     {sum(stats.values()):4d}")
    print()


def show_recent_jobs(queue: JobQueue, limit: int = 10):
    """Show recent job activity."""
    # Get recent jobs sorted by created_at desc
    recent_jobs = list(queue.jobs.find().sort("created_at", -1).limit(limit))

    if not recent_jobs:
        print("📋 No jobs found")
        return

    print(f"📋 Recent Jobs (last {len(recent_jobs)})")
    print("=" * 80)
    print(f"{'ID':12} {'Status':10} {'Command':30} {'Duration':12} {'Created':12}")
    print("-" * 80)

    for job in recent_jobs:
        job_id = job['job_id'][:8]
        status = job['status']
        command = job.get('command', 'Unknown').split('/')[-1][:28]  # Just filename

        # Calculate duration
        start = job.get('started_at')
        end = job.get('completed_at')
        duration = format_duration(start, end) if start else "N/A"

        # Format created time
        created = job['created_at'].strftime("%H:%M:%S")

        # Add status emoji
        status_emoji = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(status, '❓')

        status_display = f"{status_emoji} {status}"

        print(f"{job_id:12} {status_display:12} {command:30} {duration:12} {created:12}")

    print()


def show_running_jobs(queue: JobQueue):
    """Show currently running jobs with details."""
    running_jobs = queue.get_jobs_by_status("running")

    if not running_jobs:
        print("🔄 No currently running jobs")
        return

    print(f"🔄 Running Jobs ({len(running_jobs)})")
    print("=" * 60)

    for job in running_jobs:
        job_id = job['job_id'][:8]
        command = job['command']
        started = job.get('started_at')
        running_time = format_duration(started) if started else "N/A"
        timeout = job.get('timeout', 1800)

        print(f"   Job: {job_id}")
        print(f"   Command: {command}")
        print(f"   Running: {running_time} / {timeout}s timeout")
        print(f"   Started: {started.strftime('%Y-%m-%d %H:%M:%S') if started else 'N/A'}")
        print()


def show_failed_jobs(queue: JobQueue, limit: int = 5):
    """Show recent failed jobs with error details."""
    failed_jobs = queue.get_jobs_by_status("failed", limit=limit)

    if not failed_jobs:
        print("✅ No failed jobs")
        return

    print(f"❌ Recent Failed Jobs ({len(failed_jobs)})")
    print("=" * 60)

    for job in failed_jobs:
        job_id = job['job_id'][:8]
        command = job['command']
        error = job.get('error', 'Unknown error')
        completed = job.get('completed_at')

        print(f"   Job: {job_id}")
        print(f"   Command: {command}")
        print(f"   Error: {error}")
        print(f"   Failed: {completed.strftime('%Y-%m-%d %H:%M:%S') if completed else 'N/A'}")
        print()


def monitor_loop(queue: JobQueue, refresh_interval: int = 5):
    """Run continuous monitoring with refresh."""
    print("🎯 Job Queue Monitor")
    print("Press Ctrl+C to exit")
    print()

    try:
        while True:
            clear_screen()
            print(f"🎯 Job Queue Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Press Ctrl+C to exit")
            print()

            show_queue_status(queue)
            show_running_jobs(queue)
            show_recent_jobs(queue, limit=5)
            show_failed_jobs(queue, limit=3)

            print(f"🔄 Refreshing every {refresh_interval} seconds...")
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")


def main():
    """Main entry point for monitor."""
    parser = argparse.ArgumentParser(description="Job Queue Monitor")
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Show status once and exit (don't loop)"
    )
    parser.add_argument(
        "--failed",
        action="store_true",
        help="Show only failed jobs"
    )
    parser.add_argument(
        "--running",
        action="store_true",
        help="Show only running jobs"
    )
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

    args = parser.parse_args()

    try:
        queue = JobQueue(
            db_name=args.db_name,
            collection_name=args.collection
        )
    except Exception as e:
        print(f"❌ Failed to connect to job queue: {e}")
        return 1

    try:
        if args.failed:
            show_failed_jobs(queue, limit=20)
        elif args.running:
            show_running_jobs(queue)
        elif args.once:
            show_queue_status(queue)
            show_running_jobs(queue)
            show_recent_jobs(queue)
            show_failed_jobs(queue)
        else:
            monitor_loop(queue, args.refresh)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        queue.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())