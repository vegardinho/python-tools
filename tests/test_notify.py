from types import SimpleNamespace

import pytest

from python_tools import notify


def test_push_notification_requires_credentials(tmp_path):
    with pytest.raises(notify.PushoverKeysNotFound):
        notify.push_notification("hello", secrets_file=str(tmp_path / "missing.yaml"))


def test_push_notification_posts_to_pushover(monkeypatch, tmp_path):
    requests = []

    class Response:
        status = 200
        reason = "OK"

    class Connection:
        def __init__(self, host):
            self.host = host

        def request(self, *args):
            requests.append(args)

        def getresponse(self):
            return Response()

    monkeypatch.setattr(notify.http.client, "HTTPSConnection", Connection)

    notify.push_notification(
        "hello",
        pushover_token="token",
        pushover_key="user",
        secrets_file=str(tmp_path / "missing.yaml"),
    )

    assert requests[0][0] == "POST"
    assert "token=token" in requests[0][2]
    assert "message=hello" in requests[0][2]


def test_mail_uses_password_file_and_delegates(monkeypatch, tmp_path):
    password_file = tmp_path / "password"
    password_file.write_text("secret", encoding="utf-8")
    calls = []

    monkeypatch.setattr(
        notify._send_email,
        "send_email",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    notify.mail(
        "to@example.test",
        "Subject",
        "Body",
        "from@example.test",
        pwd_file=str(password_file),
    )

    assert calls[0][0][:3] == (
        "to@example.test",
        "Subject",
        "Body",
    )
    assert calls[0][1]["sender_email"] == "from@example.test"
    assert calls[0][1]["sender_email"] == "from@example.test"
