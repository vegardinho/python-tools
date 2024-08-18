# Python Tools <!-- omit in toc -->

A collection of custom handy tools for python.

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
