#!/usr/bin/env python3
"""
Example: Custom job with metadata and advanced features.

Shows how to use custom metadata and create more sophisticated jobs.
"""

import sys
import json
import argparse
import time
from datetime import datetime


def send_notification(message: str, webhook_url: str = None):
    """Simulate sending notification (placeholder)."""
    print(f"📧 NOTIFICATION: {message}")
    if webhook_url:
        print(f"   Webhook: {webhook_url}")


def log_metrics(job_id: str, metrics: dict):
    """Log job metrics (placeholder)."""
    print(f"📈 METRICS for {job_id}:")
    for key, value in metrics.items():
        print(f"   {key}: {value}")


def process_with_metadata(job_id: str, data_path: str, notify: bool = False):
    """Process data with advanced features."""
    start_time = time.time()

    print(f"🆔 Job ID: {job_id}")
    print(f"📂 Processing: {data_path}")
    print(f"⏰ Started: {datetime.now().isoformat()}")

    try:
        # Simulate processing
        records_processed = 0
        for i in range(10):
            time.sleep(0.5)  # Simulate work
            records_processed += 100
            print(f"   Processed {records_processed} records...")

        processing_time = time.time() - start_time

        # Log metrics
        metrics = {
            "records_processed": records_processed,
            "processing_time_seconds": round(processing_time, 2),
            "throughput_records_per_second": round(records_processed / processing_time, 2)
        }
        log_metrics(job_id, metrics)

        # Send notification if requested
        if notify:
            send_notification(
                f"Job {job_id[:8]} completed successfully! "
                f"Processed {records_processed} records in {processing_time:.1f}s"
            )

        # Output final results
        result = {
            "job_id": job_id,
            "status": "completed",
            "records_processed": records_processed,
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat()
        }

        print(f"✅ Job completed successfully!")
        print(f"📋 Final result: {json.dumps(result, indent=2)}")

        return result

    except Exception as e:
        error_msg = f"Processing failed: {e}"
        print(f"❌ {error_msg}", file=sys.stderr)

        if notify:
            send_notification(f"Job {job_id[:8]} failed: {error_msg}")

        raise


def main():
    """Main job function with argument parsing."""
    parser = argparse.ArgumentParser(description="Advanced job with metadata")
    parser.add_argument("--job-id", required=True, help="Job identifier")
    parser.add_argument("--data-path", required=True, help="Path to data file")
    parser.add_argument("--notify", action="store_true", help="Send notifications")
    parser.add_argument("--webhook", help="Webhook URL for notifications")

    try:
        args = parser.parse_args()

        # Set webhook for notifications
        if args.webhook:
            # In real implementation, you'd use the webhook
            pass

        result = process_with_metadata(
            job_id=args.job_id,
            data_path=args.data_path,
            notify=args.notify
        )

        sys.exit(0)

    except Exception as e:
        print(f"❌ Job failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()