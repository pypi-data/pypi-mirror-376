#!/usr/bin/env python3
"""
Example: Job that accepts command line arguments.

Shows how to write jobs that accept parameters.
"""

import sys
import argparse
import time


def process_data(input_file: str, output_file: str, operation: str):
    """Simulate data processing with parameters."""
    print(f"📥 Input file: {input_file}")
    print(f"📤 Output file: {output_file}")
    print(f"🔧 Operation: {operation}")

    # Simulate processing time
    time.sleep(2)

    # Simulate writing output
    with open(output_file, 'w') as f:
        f.write(f"Processed {input_file} with operation: {operation}\n")
        f.write(f"Timestamp: {time.time()}\n")

    print(f"✅ Successfully processed {input_file} -> {output_file}")


def main():
    """Parse arguments and process data."""
    parser = argparse.ArgumentParser(description="Process data files")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--operation", default="transform", help="Operation to perform")

    try:
        args = parser.parse_args()
        process_data(args.input, args.output, args.operation)
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()