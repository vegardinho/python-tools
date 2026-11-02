import logging

import pytest

from python_tools.my_logger import (
    ColoredFormatter,
    MyLogger,
    TimestampedTimedRotatingFileHandler,
    default_logger,
)


def test_colored_formatter_colors_known_log_levels():
    formatter = ColoredFormatter("%(levelname)s %(message)s", "%Y")
    record = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "hello", (), None
    )

    output = formatter.format(record)

    assert "\033[36mINFO\033[0m" in output
    assert "hello" in output


def test_logger_requires_a_handler_before_retrieval():
    logger = MyLogger(logger_name="test-no-handler")

    with pytest.raises(Exception, match="no handler"):
        logger.retrieve_logger()


def test_logger_can_write_to_a_file(tmp_path):
    logger = MyLogger(logger_name="test-file-logger")
    log_path = tmp_path / "test.log"
    logger.add_handler(level="INFO", filename=str(log_path), overwrite=True)

    logger.retrieve_logger().info("hello")
    for handler in logger.logger.handlers:
        handler.flush()

    assert "hello" in log_path.read_text(encoding="utf-8")


def test_log_directory_uses_level_names_for_default_filenames(tmp_path):
    logger = MyLogger(logger_name="test-level-filenames")

    logger.add_handler(level="DEBUG", write_to_file=True, log_dir=str(tmp_path))
    logger.add_handler(level="INFO", write_to_file=True, log_dir=str(tmp_path))

    filenames = {
        handler.baseFilename
        for handler in logger.logger.handlers
        if hasattr(handler, "baseFilename")
    }
    assert str(tmp_path / "DEBUG.log") in filenames
    assert str(tmp_path / "INFO.log") in filenames
    assert not (tmp_path / "10.log").exists()
    assert not (tmp_path / "20.log").exists()


def test_default_logger_uses_logs_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = logging.getLogger("python_tools.my_logger")
    handlers = list(logger.handlers)
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()

    try:
        default_logger(log_dir=str(tmp_path / "logs"))
        filenames = {
            handler.baseFilename
            for handler in logger.handlers
            if hasattr(handler, "baseFilename")
        }
        assert str(tmp_path / "logs" / "DEBUG.log") in filenames
        assert str(tmp_path / "logs" / "INFO.log") in filenames
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_timestamped_handler_changes_filename_on_first_emit(tmp_path):
    log_path = tmp_path / "test.log"
    handler = TimestampedTimedRotatingFileHandler(str(log_path))
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)

    handler.emit(record)

    assert handler.baseFilename != str(log_path)
    handler.close()
