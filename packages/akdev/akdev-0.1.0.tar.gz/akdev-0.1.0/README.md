# AKDev

Development tools and utilities by Aarush Kukreja.

## Installation
```bash
pip install akdev
```

## Usage
```python
from akdev import debug_info, format_code, DevLogger

# Debug information
print(debug_info([1, 2, 3]))

# Code formatting
code = "def hello(): print('world')"
print(format_code(code))

# Development logging
logger = DevLogger("MyApp")
logger.log("Application started")
print(logger.get_logs())
```
