#!/usr/bin/env python3
"""
Job Processor - Configurable worker daemon for processing jobs from queue.

This processor:
- Polls queue for pending jobs
- Executes jobs using configurable executor
- Updates job status based on exit codes
- Handles graceful shutdown on Ctrl+C
- Supports multiple concurrent workers
"""

import subprocess
import time
import signal
import sys
import os
import argparse
from typing import Optional, List, Dict, Any
from .queue import JobQueue


class JobProcessor:
    """Configurable job processor that executes jobs from queue."""

    def __init__(self,
                 workers: int = 1,
                 executor: str = "subprocess",
                 command_prefix: Optional[List[str]] = None,
                 queue_config: Optional[Dict[str, Any]] = None):
        """
        Initialize processor.

        Args:
            workers: Number of concurrent workers (default: 1)
            executor: Execution method - "subprocess" or "uv" (default: "subprocess")
            command_prefix: Custom command prefix (overrides executor)
            queue_config: Configuration for JobQueue initialization
        """
        # Initialize queue
        if queue_config is None:
            queue_config = {}
        self.queue = JobQueue(**queue_config)

        self.workers = workers
        self.running = True
        self.processes = {}  # {job_id: subprocess}

        # Configure command execution
        self.executor = executor
        if command_prefix:
            self.command_prefix = command_prefix
        elif executor == "uv":
            self.command_prefix = ["uv", "run"]
        else:  # subprocess
            self.command_prefix = []

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        print(f"🤖 Job Processor initialized")
        print(f"   Workers: {workers}")
        print(f"   Executor: {executor}")
        print(f"   Command prefix: {self.command_prefix or 'None'}")

    def shutdown(self, signum, frame):
        """Handle shutdown signal (Ctrl+C or SIGTERM)."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

        # Terminate any running processes
        for job_id, proc in self.processes.items():
            if proc.poll() is None:  # Still running
                print(f"🔸 Terminating job {job_id[:8]}")
                proc.terminate()

                # Give process 5 seconds to terminate gracefully
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Force killing job {job_id[:8]}")
                    proc.kill()

                # Mark job as failed due to interruption
                self.queue.fail_job(job_id, "Process interrupted during shutdown")

        print("🔌 Processor shutdown complete")
        sys.exit(0)

    def run(self):
        """Main processor loop."""
        print(f"🚀 Starting job processor...")
        print(f"📊 Current queue stats: {self.queue.get_job_stats()}")
        print("👀 Watching for new jobs (press Ctrl+C to stop)...")

        while self.running:
            try:
                # Start new jobs if we have available workers
                if len(self.processes) < self.workers:
                    job = self.queue.get_next_job()
                    if job:
                        self.start_job(job)

                # Check for completed processes
                self.check_completed_jobs()

                # Sleep briefly to avoid busy waiting
                time.sleep(1)

            except Exception as e:
                print(f"❌ Error in processor loop: {e}")
                time.sleep(5)  # Wait longer on error

    def start_job(self, job: Dict[str, Any]):
        """
        Start a job subprocess with timeout.

        Args:
            job: Job document from queue
        """
        job_id = job["job_id"]
        command = job["command"]
        args = job.get("args", [])
        timeout = job.get("timeout", 1800)  # Default 30 minutes

        # Build command with timeout and executor
        cmd = []

        # Add timeout wrapper if available
        timeout_cmd = self._get_timeout_command()
        if timeout_cmd:
            cmd.extend([timeout_cmd, str(timeout)])

        # Add executor prefix
        cmd.extend(self.command_prefix)

        # Add the actual command and arguments
        cmd.append(command)
        cmd.extend(args)

        try:
            # Start subprocess
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Handle text encoding automatically
                cwd=os.getcwd()  # Run from current directory
            )

            self.processes[job_id] = proc
            print(f"🔄 Started job {job_id[:8]}: {command} (timeout: {timeout}s)")

        except Exception as e:
            print(f"❌ Failed to start job {job_id[:8]}: {e}")
            self.queue.fail_job(job_id, f"Failed to start process: {e}")

    def check_completed_jobs(self):
        """Check for completed processes and update job status."""
        completed_jobs = []

        for job_id, proc in self.processes.items():
            if proc.poll() is not None:  # Process finished
                completed_jobs.append(job_id)

                try:
                    # Get process output
                    stdout, stderr = proc.communicate()
                    exit_code = proc.returncode

                    # Handle timeout (exit code 124 from 'timeout' command)
                    if exit_code == 124:
                        self.queue.fail_job(job_id, "Job timed out")
                        print(f"⏰ Job {job_id[:8]} timed out")
                    else:
                        # Normal completion - let exit code determine success/failure
                        self.queue.complete_job(job_id, stdout, stderr, exit_code)

                except Exception as e:
                    print(f"❌ Error processing completed job {job_id[:8]}: {e}")
                    self.queue.fail_job(job_id, f"Error processing completion: {e}")

        # Remove completed jobs from tracking
        for job_id in completed_jobs:
            del self.processes[job_id]

    def status(self):
        """Print current processor status."""
        stats = self.queue.get_job_stats()
        active_jobs = len(self.processes)

        print(f"\n📊 Job Processor Status:")
        print(f"   Executor: {self.executor}")
        print(f"   Command prefix: {self.command_prefix or 'None'}")
        print(f"   Active workers: {active_jobs}/{self.workers}")
        print(f"   Queue stats: {stats['pending']} pending, {stats['running']} running")
        print(f"   Completed: {stats['completed']}, Failed: {stats['failed']}")

        if self.processes:
            print(f"   Running jobs:")
            for job_id in self.processes.keys():
                print(f"     - {job_id[:8]}")

    def _get_timeout_command(self) -> Optional[str]:
        """Get available timeout command for the system."""
        # Check for timeout command availability
        for cmd in ["timeout", "gtimeout"]:
            try:
                subprocess.run([cmd, "--version"],
                             capture_output=True,
                             check=True,
                             timeout=2)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue

        print("⚠️ No timeout command found - jobs may run indefinitely")
        return None


def main():
    """Main entry point for processor."""
    parser = argparse.ArgumentParser(description="Job Queue Processor")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent workers (default: 1)"
    )
    parser.add_argument(
        "--executor",
        choices=["subprocess", "uv"],
        default="subprocess",
        help="Execution method (default: subprocess)"
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
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show processor status and exit"
    )

    args = parser.parse_args()

    # Configure queue
    queue_config = {
        "db_name": args.db_name,
        "collection_name": args.collection
    }

    processor = JobProcessor(
        workers=args.workers,
        executor=args.executor,
        queue_config=queue_config
    )

    if args.status:
        processor.status()
        return

    try:
        processor.run()
    except KeyboardInterrupt:
        # Signal handler will take care of cleanup
        pass
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()