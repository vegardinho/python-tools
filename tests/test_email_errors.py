import json
import importlib
import logging

import pytest

email_errors = importlib.import_module("python_tools.email_errors")


def make_test_logger() -> logging.Logger:
    logger = logging.getLogger("python-tools-tests.email-errors")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    return logger


def test_email_errors_resets_history_on_success(tmp_path, monkeypatch):
    history = tmp_path / "history.json"
    history.write_text(
        json.dumps(
            {
                "error": ["old"],
                "error_sent": ["2026-11-01T00:00:00+00:00"],
            }
        ),
        encoding="utf-8",
    )

    email_errors.email_errors(
        None,
        "to@example.test",
        history_file=str(history),
        logger=make_test_logger(),
    )

    assert json.loads(history.read_text(encoding="utf-8")) == {
        "error": [],
        "error_sent": [],
    }


def test_email_errors_records_failure_without_sending_when_throttled(
    tmp_path, monkeypatch
):
    history = tmp_path / "history.json"
    history.write_text(
        json.dumps({"error": [], "error_sent": ["2099-01-01T00:00:00"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(email_errors, "has_internet", lambda: True)

    email_errors.email_errors(
        RuntimeError("failed"),
        "to@example.test",
        history_file=str(history),
        logger=make_test_logger(),
    )

    data = json.loads(history.read_text(encoding="utf-8"))
    assert len(data["error"]) == 1
    assert data["error_sent"] == ["2099-01-01T00:00:00"]
