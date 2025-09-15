# Advanced Python Logging (APV)
> Flexible & powerful logging solution for Python applications

![](./.screens/preview.png)

## Table of Contents
- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation](#installation)
- [Features](#features)
- [Configuration Options](#configuration-options)
- [Usage](#usage)
    - [Basic Console Logging](#basic-console-logging)
    - [Console Logging with Details](#console-logging-with-details)
    - [File Logging with Rotation](#file-logging-with-rotation)
    - [File Logging with Compression and JSON Format](#file-logging-with-compression-and-json-format)
    - [Mixing it all together](#mixing-it-all-together)

## Introduction
APV emerged from a simple observation: despite the abundance of logging solutions, there's a glaring lack of standardization in application logging. APV is my response to this challenge – a logging library that doesn't aim to revolutionize the field, but rather to streamline it.

## Requirements
- Python 3

## Installation

### From PyPI
```bash
pip install apv
```

### From Source
```bash
git clone https://github.com/acidvegas/apv
cd apv
pip install .
```

## Features
- **Console Logging with Colors**: Enhanced readability with colored log messages in the console.
- **File Logging**: Write logs to files with support for log rotation based on size and number of backups.
- **Log Compression**: Automatically compress old log files using gzip to save disk space.
- **JSON Logging**: Output logs in JSON format for better structure and integration with log management systems.
- **Syslog Capabilities**: Out logs (optionally in JSON) to the machines syslog.
- **Detailed Log Messages**: Option to include module name, function name, and line number in log messages.

## Configuration Options

The `setup_logging` function accepts the following keyword arguments to customize logging behavior:

| Name              | Default                  | Description                                                                   |
|-------------------|--------------------------|-------------------------------------------------------------------------------|
| `level`           | `INFO`                   | The logging level. *(`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)*        |
| `date_format`     | `'%Y-%m-%d %H:%M:%S'`    | The date format for log messages.                                             |
| `log_to_disk`     | `False`                  | Whether to log to disk.                                                       |
| `max_log_size`    | `10*1024*1024` *(10 MB)* | The maximum size of log files before rotation *(in bytes)*.                   |
| `max_backups`     | `7`                      | The maximum number of backup log files to keep.                               |
| `log_file_name`   | `'app'`                  | The base name of the log file.                                                |
| `json_log`        | `False`                  | Whether to log in JSON format.                                                |
| `show_details`    | `False`                  | Whether to include module name, function name, & line number in log messages. |
| `compress_backups`| `False`                  | Whether to compress old log files using gzip.                                 |
| `syslog`          | `False`                  | Whether to send logs to syslog.                                               |

## Usage

### Basic Console Logging

```python
import logging
import apv

# Set up basic console logging
apv.setup_logging(level='INFO')

logging.info('This is an info message.')
logging.error('This is an error message.')
```

### Console Logging with Details

```python
import logging
import apv

# Set up console logging with detailed information
apv.setup_logging(level='DEBUG', show_details=True)

logging.debug('Debug message with details.')
```

### File Logging with Rotation

```python
import logging
import apv

# Set up file logging with log rotation
apv.setup_logging(
    level='INFO',
    log_to_disk=True,
    max_log_size=10*1024*1024,  # 10 MB
    max_backups=5,
    log_file_name='application_log'
)

logging.info('This message will be logged to a file.')
```

### File Logging with Compression and JSON Format

```python
import logging
import apv

# Set up file logging with compression and JSON format
apv.setup_logging(
    level='DEBUG',
    log_to_disk=True,
    max_log_size=5*1024*1024,  # 5 MB
    max_backups=7,
    log_file_name='json_log',
    json_log=True,
    compress_backups=True
)

logging.debug('This is a debug message in JSON format.')
```

### Syslog Logging

```python
import logging
import apv

# Set up syslog logging
apv.setup_logging(level='INFO', syslog=True)

logging.info('This message will be sent to syslog.')
logging.error('Error messages are also sent to syslog.')
```

### Syslog Logging with JSON Format

```python
import logging
import apv

# Set up syslog logging with JSON format
apv.setup_logging(level='DEBUG', syslog=True, json_log=True)

logging.debug('This debug message will be sent to syslog in JSON format.')
logging.info('Info messages are also sent as JSON to syslog.')
```

### Syslog Logging with Details

```python
import logging
import apv

# Set up syslog logging with detailed information
apv.setup_logging(level='DEBUG', syslog=True, show_details=True)

logging.debug('This debug message will include module, function, and line details in syslog.')
```


### Mixing it all together

```python
import logging
import apv

# Set up logging to all handlers
apv.setup_logging(
    level='DEBUG',
    log_to_disk=True,
    max_log_size=10*1024*1024,
    max_backups=7,
    log_file_name='app',
    json_log=True,
    compress_backups=True,
    show_details=True,
    syslog=True
)
```

---

###### Mirrors: [acid.vegas](https://git.acid.vegas/apv) • [SuperNETs](https://git.supernets.org/acidvegas/apv) • [GitHub](https://github.com/acidvegas/apv) • [GitLab](https://gitlab.com/acidvegas/apv) • [Codeberg](https://codeberg.org/acidvegas/apv)
