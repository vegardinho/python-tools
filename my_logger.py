import logging
from logging import Formatter
import sys
from copy import copy
from logging.handlers import TimedRotatingFileHandler

class ColoredFormatter(Formatter):

    MAPPING = {
        'DEBUG'   : 37, # grey
        'INFO'    : 36, # cyan
        'WARNING' : 33, # yellow
        'ERROR'   : 31, # red
        'CRITICAL': 41, # white, red fill
    }

    PREFIX = '\033['
    SUFFIX = '\033[0m'

    def __init__(self, pattern, date_fmt):
        Formatter.__init__(self, pattern, datefmt=date_fmt)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = ColoredFormatter.MAPPING.get(levelname, 37) # default white
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format(ColoredFormatter.PREFIX, seq, levelname, ColoredFormatter.SUFFIX)
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


class MyLogger:

    FORMAT = '%(asctime)s %(filename)s [%(levelname)s] %(funcName)s:%(lineno)-6s %(message)s'
    DATE_FMT = "%Y-%m-%d %H:%M:%S"
    FORMATTER = ColoredFormatter(FORMAT, DATE_FMT)

    def __init__(self, logger_base_level='DEBUG', logger_name=__name__):
        """
        :param logger_base_level:   Handlers only receive logs from this level upwards.
        :param logger_name:         Name used for storing logger in internal logger hierarchy. Should be exclusive.
        """

        self.logger_level = getattr(logging, logger_base_level)

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self.logger_level)
        self.logger.propagate = False


    # Add handler for logging to std.out or file. If file handler, batch store log files by week.
    def add_handler(self, level="NOTSET", filename=None, overwrite=False, max_log_files=10):
        """
        :param level:           Logging level. Defaults to self.logger level.
        :param filename:        If provided, add filehandler with filename, else add streamhandler.
        :param overwrite:       Wether to overwrite log file on run.
        :param max_log_files    Maximum number of weekly log files to keep.
        :return:                MyLogger object.
        """
        if filename == None:
            handler = logging.StreamHandler(sys.stdout)
        elif overwrite:
            handler = logging.FileHandler(mode="w", filename=filename)
        else:
            handler = TimedRotatingFileHandler(filename, when='W0', backupCount=max_log_files)
        handler.setFormatter(MyLogger.FORMATTER)
        handler.setLevel(level)
        self.logger.addHandler(handler)
        return self

    # Set level on logger-level (may affect handler-level output)
    def set_logger_level(self, new_level):
        self.logger_level = getattr(logging, new_level)
        self.logger.setLevel(self.logger_level)
        return

    def retrieve_logger(self):
        if not self.logger.hasHandlers():
            raise Exception("Logger has no handler, and will not produce any logs. Please add at least one handler.")
        return self.logger


# Test use case:
if __name__ == '__main__':
    log = MyLogger(logger_base_level="DEBUG").add_handler(level="DEBUG").retrieve_logger()

    log.debug("hei")
    log.info("hei")
    log.warning("hei")
    log.error("hei")
    log.critical("hei")
