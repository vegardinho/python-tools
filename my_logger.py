import logging
from logging import Formatter
import sys
from copy import copy
from logging.handlers import TimedRotatingFileHandler

from i_o_utilities import create_files


class ColoredFormatter(Formatter):
    """
    A custom formatter to add colors to log levels for better readability in the console.
    """

    MAPPING = {
        "DEBUG": 37,  # grey
        "INFO": 36,  # cyan
        "WARNING": 33,  # yellow
        "ERROR": 31,  # red
        "CRITICAL": 41,  # white, red fill
    }

    PREFIX = "\033["
    SUFFIX = "\033[0m"

    def __init__(self, pattern, date_fmt):
        """
        Initialize the ColoredFormatter with a pattern and date format.

        :param pattern: The log message format pattern.
        :param date_fmt: The date format pattern.
        """
        Formatter.__init__(self, pattern, datefmt=date_fmt)

    def format(self, record):
        """
        Format the log record with colors based on the log level.

        :param record: The log record to format.
        :return: The formatted log record with colors.
        """
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = ColoredFormatter.MAPPING.get(levelname, 37)  # default white
        colored_levelname = ("{0}{1}m{2}{3}").format(
            ColoredFormatter.PREFIX, seq, levelname, ColoredFormatter.SUFFIX
        )
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


class MyLogger:
    """
    A custom logger class to handle logging with colored output and file rotation.
    """

    FORMAT = (
        "%(asctime)s %(filename)s [%(levelname)s] %(funcName)s:%(lineno)-6s %(message)s"
    )
    DATE_FMT = "%Y-%m-%d %H:%M:%S"
    FORMATTER = ColoredFormatter(FORMAT, DATE_FMT)

    def __init__(self, logger_base_level="DEBUG", logger_name=__name__):
        """
        Initialize the MyLogger instance.

        :param logger_base_level: Handlers only receive logs from this level upwards.
        :param logger_name: Name used for storing logger in internal logger hierarchy. Should be exclusive.
        """
        self.logger_level = getattr(logging, logger_base_level)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self.logger_level)
        self.logger.propagate = False

    def add_handler(
        self,
        level="NOTSET",
        filename=None,
        overwrite=False,
        rollover_interval=7,
        rollover_type="D",
        max_log_files=10,
    ):
        """
        Add a handler for logging to std.out or file. If file handler, batch store log files by week.

        :param level: Logging level. Defaults to self.logger level.
        :param filename: If provided, add filehandler with filename, else add streamhandler.
        :param overwrite: Whether to overwrite log file on run.
        :param rollover_interval: Number of days between log rotations.
        :param rollover_type: Type of rollover interval (e.g., 'D' for days, 'S' for seconds). Defaults to days.
        :param max_log_files: Maximum number of log files to keep.
        :return: MyLogger object.
        """
        if filename:
            create_files(filename)
            if overwrite:
                handler = logging.FileHandler(mode="w", filename=filename)
            else:
                if rollover_interval == 7:
                    rollover_type = "W0"  # Reset weekly log files on Monday
                handler = TimedRotatingFileHandler(
                    filename,
                    when=rollover_type,
                    interval=rollover_interval,
                    backupCount=max_log_files,
                )
        else:
            handler = logging.StreamHandler(sys.stdout)

        handler.setFormatter(MyLogger.FORMATTER)
        handler.setLevel(level)

        # Check if the handler already exists
        if not any(isinstance(h, type(handler)) for h in self.logger.handlers):
            self.logger.addHandler(handler)
        return self

    def set_logger_level(self, new_level):
        """
        Set the logging level on the logger.

        :param new_level: The new logging level to set.
        """
        self.logger_level = getattr(logging, new_level)
        self.logger.setLevel(self.logger_level)
        return

    def retrieve_logger(self):
        """
        Retrieve the logger instance. Raises an exception if no handlers are added.

        :return: The logger instance.
        """
        if not self.logger.hasHandlers():
            raise Exception(
                "Logger has no handler, and will not produce any logs. Please add at least one handler."
            )
        return self.logger


def default_logger(log_file=None, logger_base_level="DEBUG"):
    """
    Configure logging for the application.

    :param log_file: Path to the log file.
    :param logger_base_level: Base logging level.
    :return: Configured logger instance.
    """
    logger = (
        MyLogger(logger_base_level=logger_base_level)
        .add_handler(level="INFO")
        .add_handler(level="INFO", filename=log_file)
        .retrieve_logger()
    )
    return logger


# Test use case:
if __name__ == "__main__":
    log = default_logger()

    log.debug("hei")
    log.info("hei")
    log.warning("hei")
    log.error("hei")
    log.critical("hei")
