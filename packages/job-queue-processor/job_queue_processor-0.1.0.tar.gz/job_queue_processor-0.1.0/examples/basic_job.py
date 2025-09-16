#!/usr/bin/env python3
"""
Example: Basic job that processes some data and exits.

This demonstrates the minimal pattern for a job script:
- Do work
- Print results to stdout
- Exit with 0 for success, non-zero for failure
"""

import sys
import time
import random


def main():
    """Simulate some basic data processing work."""
    try:
        print("🔄 Starting basic job...")

        # Simulate work
        work_time = random.uniform(1, 5)
        print(f"📊 Processing data for {work_time:.1f} seconds...")
        time.sleep(work_time)

        # Simulate result
        result = random.randint(100, 999)
        print(f"✅ Processing complete! Result: {result}")

        # Success
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()