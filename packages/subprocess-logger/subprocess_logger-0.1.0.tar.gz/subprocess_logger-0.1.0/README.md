# subprocess-logger

Consolidated handler for subprocess logging in Python.

## Overview

`subprocess-logger` provides a unified way to capture and forward output from Python subprocesses to the standard logging system. It is useful for applications that spawn subprocesses and want to collect their stdout and stderr streams in a thread-safe, structured manner.

## Features

- Collects stdout and stderr from subprocesses and logs them using Python's `logging` module.
- Allows log level customization at global and per process level for stdout and stderr.
- Thread-safe collection and dispatching of logs.
- Easy integration with existing logging configurations.

## Installation

```sh
pip install subprocess-logger
```

## Usage

Below is a basic usage example:

```python
import logging
import subprocess
from subprocess_logger import install

# Configure root logger to print to console
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

# Create a collector instance
collector = install(stdout_level=logging.INFO, stderr_level=logging.WARNING)

# Start a subprocess that prints to stdout and stderr
proc = subprocess.Popen(
    ["python", "-c", "import sys; print('hello from stdout'); sys.stderr.write('hello from stderr\\n')"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Attach the subprocess to the collector
collector.attach(proc, logger_name="demo_subprocess")

# Wait for the subprocess to finish
proc.wait()

# Stop the collector (waits for all logs to be processed)
collector.stop()
```

## Testing

To run unit tests, use the following command:

```sh
pytest
```

Or, if you have `tox` installed:

```sh
tox
```

## License

This project is licensed under the MIT License.
