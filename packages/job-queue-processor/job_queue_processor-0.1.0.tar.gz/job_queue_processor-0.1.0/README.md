# Job Queue Processor

A simple, extensible job queue processor with MongoDB backend. Perfect for distributed task processing, background jobs, and workflow automation.

## Features

- 🚀 **Simple & Fast**: Minimal setup, just set `MONGODB_URI` and go
- 📦 **Easy Installation**: Install with `uv pip install job-queue-processor`
- 🔧 **Configurable**: Support for custom databases, collections, and metadata
- ⚡ **Multiple Executors**: Built-in support for subprocess and `uv run`
- 👥 **Multi-Worker**: Concurrent job processing with configurable workers
- 🛡️ **Robust**: Timeout handling, graceful shutdown, and error recovery
- 📊 **Monitoring**: Real-time queue statistics and job history
- 🔄 **Bulk Operations**: Submit multiple jobs efficiently
- 🏷️ **Metadata Support**: Add custom fields to jobs for organization

## Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install job-queue-processor

# Using pip
pip install job-queue-processor
```

### Setup

1. **Start MongoDB** (locally or use a cloud service)

2. **Set environment variable**:
   ```bash
   export MONGODB_URI="mongodb://localhost:27017"
   # Or create .env file with MONGODB_URI=mongodb://localhost:27017
   ```

3. **Start processing jobs**:
   ```bash
   # Start the processor
   job-process --workers 3
   ```

4. **Submit jobs** (in another terminal):
   ```bash
   # Submit a simple job
   job-submit "python script.py"

   # Submit with arguments
   job-submit "script.py" --args --input data.csv --output results.json

   # Monitor progress
   job-monitor
   ```

## Usage Examples

### CLI Usage

```bash
# Basic job submission
job-submit "examples/basic_job.py"

# Job with arguments and timeout
job-submit "script.py" --args --input data.csv --timeout 600

# Job with custom metadata
job-submit "script.py" --metadata '{"priority": 1, "team": "data"}'

# Bulk submission from JSON
job-submit --bulk '[
  {"command": "script1.py", "timeout": 300},
  {"command": "script2.py", "args": ["--mode", "fast"]}
]'

# Process jobs with multiple workers
job-process --workers 5 --executor uv

# Monitor queue
job-monitor --refresh 3
job-monitor --failed  # Show only failed jobs
job-submit --stats    # Quick stats
```

### Python API

```python
from job_queue_processor import JobQueue, JobProcessor

# Submit jobs
queue = JobQueue()

# Basic job
job_id = queue.submit_job("script.py")

# Job with arguments and metadata
job_id = queue.submit_job(
    "process_data.py",
    args=["--input", "data.csv", "--output", "results.json"],
    timeout=600,
    metadata={"priority": 1, "team": "analytics"}
)

# Bulk submission
jobs = [
    {
        "command": "task1.py",
        "args": ["--mode", "fast"],
        "timeout": 300,
        "metadata": {"batch": "morning_run"}
    },
    {
        "command": "task2.py",
        "timeout": 600,
        "metadata": {"batch": "morning_run"}
    }
]
job_ids = queue.submit_bulk_jobs(jobs)

# Check status
stats = queue.get_job_stats()
print(f"Pending: {stats['pending']}, Running: {stats['running']}")

queue.close()
```

### Process Jobs

```python
from job_queue_processor import JobProcessor

# Start processor
processor = JobProcessor(
    workers=3,
    executor="subprocess",  # or "uv"
    queue_config={
        "db_name": "my_jobs",
        "collection_name": "tasks"
    }
)

processor.run()  # Blocks and processes jobs
```

## Configuration

### Environment Variables

The only required configuration is the MongoDB connection:

```bash
# Local MongoDB
MONGODB_URI=mongodb://localhost:27017

# MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# MongoDB with auth
MONGODB_URI=mongodb://user:pass@localhost:27017
```

### Custom Configuration

```python
from job_queue_processor import JobQueue, JobProcessor

# Custom database and collection
queue = JobQueue(
    mongo_uri="mongodb://localhost:27017",
    db_name="my_project",
    collection_name="background_jobs"
)

# Custom processor configuration
processor = JobProcessor(
    workers=5,
    executor="uv",  # Use uv run instead of direct subprocess
    command_prefix=["python", "-u"],  # Custom command prefix
    queue_config={
        "db_name": "my_project",
        "collection_name": "background_jobs"
    }
)
```

## Job Script Requirements

Jobs can be any executable that follows these simple rules:

```python
#!/usr/bin/env python3
import sys

try:
    # Do your work here
    result = process_data()
    print(f"Success: {result}")  # stdout for results
    sys.exit(0)  # 0 = success

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)  # stderr for errors
    sys.exit(1)  # non-zero = failure
```

**That's it!** No special imports or setup required.

## Examples

The `examples/` directory contains:

- **`basic_job.py`** - Simple job template
- **`job_with_args.py`** - Job that accepts command line arguments
- **`custom_handler.py`** - Advanced job with metadata and logging
- **`bulk_submit.py`** - Bulk job submission patterns
- **`submit_examples.py`** - Various submission examples

Run the examples:
```bash
# Try the examples
python examples/submit_examples.py

# Submit example jobs
job-submit "examples/basic_job.py"
job-submit "examples/job_with_args.py" --args --input test.csv --output out.json

# Process them
job-process --workers 2
```

## Monitoring

### Real-time Monitoring
```bash
# Continuous monitoring (refreshes every 5 seconds)
job-monitor

# Custom refresh rate
job-monitor --refresh 10

# Show status once and exit
job-monitor --once

# Show only failed jobs
job-monitor --failed

# Show only running jobs
job-monitor --running
```

### Quick Stats
```bash
job-submit --stats
```

## Advanced Usage

### Custom Metadata

Add custom fields to organize and track jobs:

```python
queue.submit_job(
    "ml_training.py",
    metadata={
        "project": "recommendation_engine",
        "priority": 1,
        "owner": "data-team",
        "experiment_id": "exp_001",
        "gpu_required": True
    }
)
```

### Multiple Queues

Use different databases or collections for different purposes:

```python
# High priority queue
priority_queue = JobQueue(db_name="priority_jobs")

# Background tasks queue
background_queue = JobQueue(db_name="background_jobs")

# Long-running jobs
long_queue = JobQueue(
    db_name="long_jobs",
    collection_name="training_jobs"
)
```

### Custom Executors

```python
# Use uv for Python package management
processor = JobProcessor(executor="uv")

# Custom command prefix
processor = JobProcessor(command_prefix=["docker", "run", "my-image"])

# No timeout (for very long jobs)
processor = JobProcessor(command_prefix=["python", "-u"])
```

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │  Processor  │    │   MongoDB   │
│             │    │             │    │             │
│ submit_job()│───▶│ get_next()  │───▶│    jobs     │
│             │    │             │    │ collection  │
│             │    │ execute()   │    │             │
│             │    │             │    │             │
│ monitor()   │◀───│ complete()  │◀───│             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Job Lifecycle

```
pending → running → completed/failed
```

### MongoDB Schema

```javascript
{
  "job_id": "uuid",
  "command": "script.py",
  "args": ["--input", "data.csv"],
  "timeout": 1800,
  "status": "pending|running|completed|failed",
  "created_at": "timestamp",
  "started_at": "timestamp",
  "completed_at": "timestamp",
  "stdout": "process output",
  "stderr": "error output",
  "exit_code": 0,
  "metadata": {
    "priority": 1,
    "team": "analytics"
  }
}
```

## Development

### Setup Development Environment

```bash
git clone <repository>
cd job-queue-processor

# Install with development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ examples/
ruff check src/ examples/
```

### Building and Publishing

```bash
# Build package
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- **Documentation**: This README and inline code comments
- **Examples**: See `examples/` directory
- **Issues**: Report bugs and request features on GitHub
- **MongoDB**: Any MongoDB-compatible database (local, Atlas, etc.)

---

**Ready to get started?** Just set `MONGODB_URI` and run `job-process`! 🚀