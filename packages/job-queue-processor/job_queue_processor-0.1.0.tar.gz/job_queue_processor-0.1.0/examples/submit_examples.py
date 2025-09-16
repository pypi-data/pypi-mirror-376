#!/usr/bin/env python3
"""
Example: Different ways to submit jobs using the CLI and Python API.

This script demonstrates various job submission patterns.
"""

import subprocess
import sys
from job_queue_processor import JobQueue


def cli_examples():
    """Show CLI submission examples."""
    print("🖥️  CLI Submission Examples")
    print("=" * 50)

    examples = [
        {
            "description": "Basic job",
            "command": ["job-submit", "examples/basic_job.py"]
        },
        {
            "description": "Job with arguments",
            "command": ["job-submit", "examples/job_with_args.py",
                       "--args", "--input", "data.csv", "--output", "result.json"]
        },
        {
            "description": "Job with custom timeout",
            "command": ["job-submit", "examples/basic_job.py", "--timeout", "300"]
        },
        {
            "description": "Job with metadata",
            "command": ["job-submit", "examples/basic_job.py",
                       "--metadata", '{"priority": 1, "team": "data"}']
        },
        {
            "description": "Python inline job",
            "command": ["job-submit", "python",
                       "--args", "-c", "print('Hello from inline job')"]
        }
    ]

    for example in examples:
        print(f"\n📋 {example['description']}:")
        print(f"   {' '.join(example['command'])}")

    print(f"\n💡 To run these examples, copy and paste the commands above")


def python_api_examples():
    """Show Python API submission examples."""
    print("\n🐍 Python API Examples")
    print("=" * 50)

    try:
        queue = JobQueue()

        print("\n1. Basic job submission:")
        job_id = queue.submit_job("examples/basic_job.py")
        print(f"   Submitted job: {job_id[:8]}")

        print("\n2. Job with arguments:")
        job_id = queue.submit_job(
            "examples/job_with_args.py",
            args=["--input", "test.csv", "--output", "out.json"],
            timeout=300
        )
        print(f"   Submitted job: {job_id[:8]}")

        print("\n3. Job with metadata:")
        job_id = queue.submit_job(
            "examples/custom_handler.py",
            args=["--job-id", "custom-001", "--data-path", "/tmp/data"],
            metadata={
                "priority": 1,
                "team": "analytics",
                "project": "data-pipeline"
            }
        )
        print(f"   Submitted job: {job_id[:8]}")

        print("\n4. Bulk submission:")
        jobs = [
            {
                "command": "examples/basic_job.py",
                "timeout": 60,
                "metadata": {"batch": "demo", "index": i}
            }
            for i in range(3)
        ]
        job_ids = queue.submit_bulk_jobs(jobs)
        print(f"   Submitted {len(job_ids)} jobs")

        # Show current stats
        stats = queue.get_job_stats()
        print(f"\n📊 Current queue stats: {stats}")

        queue.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure MongoDB is running and MONGODB_URI is set")


def monitoring_examples():
    """Show monitoring command examples."""
    print("\n📊 Monitoring Examples")
    print("=" * 50)

    commands = [
        ("Show current stats", "job-submit --stats"),
        ("Monitor continuously", "job-monitor"),
        ("Show status once", "job-monitor --once"),
        ("Show only failed jobs", "job-monitor --failed"),
        ("Show only running jobs", "job-monitor --running"),
        ("Process jobs", "job-process --workers 3"),
        ("Process with uv executor", "job-process --executor uv --workers 2")
    ]

    for description, command in commands:
        print(f"\n📋 {description}:")
        print(f"   {command}")


def main():
    """Show all examples."""
    print("🚀 Job Queue Processor - Submission Examples")
    print("=" * 60)

    cli_examples()
    python_api_examples()
    monitoring_examples()

    print("\n" + "=" * 60)
    print("💡 Next steps:")
    print("   1. Start the processor: job-process --workers 2")
    print("   2. Submit some jobs using the examples above")
    print("   3. Monitor progress: job-monitor")


if __name__ == "__main__":
    main()