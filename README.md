# Python Tools <!-- omit in toc -->

A collection of custom handy tools for python.

The reusable modules are provided under the `python_tools` package namespace:

```python
from python_tools.email_errors import email_errors
from python_tools.my_logger import MyLogger
from python_tools.notify import PasswordNotExists
```

The supported public modules and symbols are explicitly listed in each
module's `__all__`. The SMTP transport is internal (`python_tools._send_email`)
and should be accessed through `python_tools.notify.mail`.

## Testing

The tests are in `tests/` and use `pytest`. This project uses
[uv](https://docs.astral.sh/uv/) for dependency and environment management.
Set up the environment and run the tests with:

```sh
uv sync
uv run pytest -q
```

The suite tests:

- file creation and age/pattern-based file removal
- logger formatting, handler setup, file output, and timestamped rotation
- SMTP message creation, HTML content, attachments, and missing files
- Pushover credential validation and HTTP requests
- email password lookup and delegation
- error-history reset and throttled failure recording
- basic scraper URL validation

Scraper tests are skipped when the optional scraper dependencies are not
installed. Enable them with:

```sh
uv sync --extra scraper
uv run pytest -q
```

## Contents

- [My Logger (my_logger.py)](#my-logger-my_loggerpy)
  - [Levels](#levels)
  - [Setup](#setup)
  - [Example](#example)

## My Logger \(my_logger.py\)

Wrapper for `logging` package in Python. Key features:

- Colored formatting.
- Automatic deletion of old logs.
- Predefined levels with corresponding color.
- Add any number of handlers, including simulatneous stdout and file write.

### Levels

`'DEBUG'   : 37, # grey`</br>
`'INFO'    : 36, # cyan`</br>
`'WARNING' : 33, # yellow`</br>
`'ERROR'   : 31, # red`</br>
`'CRITICAL': 41, # white, red fill`</br>

### Setup

Initialize object, add handlers and retrieve logger.

### Methods

- add_handler(level="NOTSET", filename=None, overwrite=False, max_log_files=10)
- set_logger_level(new_level)
- retrieve_logger()

### Example

The example below adds four handlers, of which one logs to stdout, and the rest to specific files.

`log_obj = MyLogger()`</br>
`log_obj.add_handler(level="INFO")`</br>
`log_obj.add_handler(level="WARNING", filename="logs/err.log")`</br>
`log_obj.add_handler(level="INFO", filename="logs/info.log")`</br>
`log_obj.add_handler(level="DEBUG", filename="logs/all.log")`</br>
`logger = log_obj.retrieve_logger()`
