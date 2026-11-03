import json
import importlib
import arrow
import pytest

email_errors = importlib.import_module("python_tools.email_errors")


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(("info", message))

    def debug(self, message):
        self.messages.append(("debug", message))

    def warning(self, message):
        self.messages.append(("warning", message))

    def error(self, message):
        self.messages.append(("error", message))


def test_email_errors_initializes_empty_history(tmp_path):
    history = tmp_path / "history.json"
    logger = RecordingLogger()

    email_errors.email_errors(
        None,
        "to@example.test",
        history_file=str(history),
        logger=logger,
    )

    assert (
        "info",
        "History file is empty; initializing error and email history.",
    ) in logger.messages


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

    logger = RecordingLogger()
    email_errors.email_errors(
        None,
        "to@example.test",
        history_file=str(history),
        logger=logger,
    )

    assert json.loads(history.read_text(encoding="utf-8")) == {
        "error": [],
        "error_sent": [],
    }
    assert ("info", "Reading existing error and email history.") in logger.messages


def test_email_errors_records_failure_without_sending_when_throttled(
    tmp_path, monkeypatch
):
    history = tmp_path / "history.json"
    history.write_text(
        json.dumps(
            {
                "error": [],
                "error_sent": [
                    "2026-10-01T00:00:00",
                    "2026-10-15T00:00:00",
                    "2026-11-02T00:00:00",
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(email_errors, "has_internet", lambda: True)

    logger = RecordingLogger()
    email_errors.email_errors(
        RuntimeError("failed"),
        "to@example.test",
        history_file=str(history),
        logger=logger,
    )

    data = json.loads(history.read_text(encoding="utf-8"))
    assert len(data["error"]) == 1
    assert data["error_sent"] == [
        "2026-10-01T00:00:00",
        "2026-10-15T00:00:00",
        "2026-11-02T00:00:00",
    ]
    assert (
        "warning",
        "Next error email will be sent in 3 day(s).",
    ) in logger.messages


@pytest.mark.parametrize("interval_index", [0, 1, 2, -1])
def test_email_errors_sends_at_configured_intervals(
    tmp_path, monkeypatch, interval_index
):
    intervals = email_errors.SEND_INTERVALS
    interval = intervals[interval_index]
    sent_count = len(intervals) if interval_index == -1 else interval_index
    history = tmp_path / "history.json"
    now = arrow.get("2026-11-03T00:00:00+00:00")
    last_send = now.shift(days=-interval)
    history.write_text(
        json.dumps(
            {
                "error": [],
                "error_sent": [last_send.format()] * sent_count,
            }
        ),
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setattr(email_errors, "NOW", now)
    monkeypatch.setattr(email_errors, "has_internet", lambda: True)
    monkeypatch.setattr(
        email_errors.notify,
        "mail",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    email_errors.email_errors(
        RuntimeError("failed"),
        "to@example.test",
        history_file=str(history),
        logger=RecordingLogger(),
    )

    data = json.loads(history.read_text(encoding="utf-8"))
    assert len(calls) == 1
    assert len(data["error_sent"]) == sent_count + 1


def test_email_errors_reuses_final_interval_after_configured_intervals(
    tmp_path, monkeypatch
):
    intervals = email_errors.SEND_INTERVALS
    now = arrow.get("2026-11-03T00:00:00+00:00")
    history = tmp_path / "history.json"
    history.write_text(
        json.dumps(
            {
                "error": [],
                "error_sent": [now.shift(days=-intervals[-1]).format()]
                * (len(intervals) + 1),
            }
        ),
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setattr(email_errors, "NOW", now)
    monkeypatch.setattr(email_errors, "has_internet", lambda: True)
    monkeypatch.setattr(
        email_errors.notify,
        "mail",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    email_errors.email_errors(
        RuntimeError("failed"),
        "to@example.test",
        history_file=str(history),
        logger=RecordingLogger(),
    )

    assert len(calls) == 1


def test_email_errors_passes_custom_password_file_to_mail(
    tmp_path, monkeypatch
):
    history = tmp_path / "history.json"
    calls = []
    monkeypatch.setattr(email_errors, "has_internet", lambda: True)
    monkeypatch.setattr(
        email_errors.notify,
        "mail",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    email_errors.email_errors(
        RuntimeError("failed"),
        "to@example.test",
        history_file=str(history),
        logger=RecordingLogger(),
        pwd_file="config/.email_pwd",
    )

    assert calls[0][1]["pwd_file"] == "config/.email_pwd"
