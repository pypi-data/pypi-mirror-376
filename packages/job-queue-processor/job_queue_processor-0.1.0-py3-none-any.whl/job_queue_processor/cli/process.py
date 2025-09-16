#!/usr/bin/env python3
"""
Job Processor CLI - Process jobs from the queue.

This CLI starts the job processor daemon.
"""

import sys
from ..processor import main

if __name__ == "__main__":
    main()