# SPMC-Py

A high-performance Single Producer Multiple Consumer (SPMC) queue implementation in Cython.

## Features

- **Lock-free**: Uses atomic operations for thread-safe communication
- **High performance**: Cython implementation compiled to C++
- **Multiple readers**: Support for multiple consumer threads
- **Python objects**: Can store any Python object in the queue
- **Memory efficient**: Ring buffer with configurable size

## Installation

Build from source using uv:

```bash
uv build
uv pip install -e .
```

## Usage

```python
from spmc_py import SPMCQueue

# Create queue (size must be power of 2)
queue = SPMCQueue(1024)

# Producer thread
queue.write("Hello, World!")
queue.write({"data": 42})

# Consumer threads
reader1 = queue.get_reader()
reader2 = queue.get_reader()

# Read next message (returns None if no data)
msg = reader1.read()

# Read all available messages and return the last one
last_msg = reader2.read_last()
```

## Performance

See `main.py` for performance benchmarks comparing latency across multiple reader threads.

## Requirements

- Python 3.11+
- Cython 3.0+
