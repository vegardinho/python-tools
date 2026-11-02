from email import policy
from email.parser import BytesParser

import pytest

from python_tools import _send_email as send_email


class FakeSMTP:
    instances = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.messages = []
        self.login_args = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def login(self, sender, password):
        self.login_args = (sender, password)

    def sendmail(self, sender, receiver, message):
        self.messages.append((sender, receiver, message))


def test_send_email_sends_html_and_attachment(monkeypatch, tmp_path):
    attachment = tmp_path / "report.txt"
    attachment.write_text("report", encoding="utf-8")
    FakeSMTP.instances.clear()
    monkeypatch.setattr(send_email.smtplib, "SMTP_SSL", FakeSMTP)

    send_email.send_email(
        "to@example.test",
        "Subject",
        "<b>Hello</b>",
        str(attachment),
        sender_email="from@example.test",
        password="secret",
        html=True,
    )

    smtp = FakeSMTP.instances[0]
    assert smtp.login_args == ("from@example.test", "secret")
    message = BytesParser(policy=policy.default).parsebytes(
        smtp.messages[0][2].encode()
    )
    assert message["Subject"] == "Subject"
    assert message.get_body(("html",)).get_content() == "<b>Hello</b>"
    attachments = [
        part for part in message.iter_attachments() if part.get_filename() == "report.txt"
    ]
    assert len(attachments) == 1


def test_send_email_rejects_missing_attachment(tmp_path):
    with pytest.raises(FileNotFoundError, match="Invalid file specified"):
        send_email.send_email(
            "to@example.test",
            "Subject",
            "Body",
            str(tmp_path / "missing.txt"),
            sender_email="from@example.test",
            password="secret",
        )
