import os
import json
import http.client
import urllib
import send_email


def push_notification(text, pushover_token, pushover_key):
    secrets_file = ".secrets"
    if os.path.exists(secrets_file):
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
            pushover_key = secrets.get("pushover_key", "")
    else:
        raise FileNotFoundError(
            "The .secrets file does not exist and pushover_key is not provided."
        )

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST",
        "/1/messages.json",
        urllib.parse.urlencode(
            {
                "token": pushover_token,
                "user": pushover_key,
                "message": text,
                "html": 1,  # Enable html formatting
            }
        ),
        {"Content-type": "application/x-www-form-urlencoded"},
    )
    conn.getresponse()


def mail(recipient, subj, text, files=None):
    send_email.send_email(recipient, subj, text, files)


if __name__ == "__main__":
    text = 'Test med html:\n<a href="http://example.com/">word</a>'
    push_notification(text)
