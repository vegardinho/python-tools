import os
import http.client
import urllib
import send_email
from my_logger import default_logger
import yaml

logger = default_logger()


class PushoverKeysNotFound(Exception):
    pass


class PushoverNotificationFailed(Exception):
    pass


def push_notification(
    text, pushover_token=None, pushover_key=None, secrets_file="./input/secrets.yaml"
):
    logger.info("Starting push_notification function")
    secrets_file = os.path.abspath(secrets_file)  # Resolve the absolute path
    logger.debug(f"Resolved secrets file path: {secrets_file}")

    if os.path.exists(secrets_file):
        with open(secrets_file, "r") as f:
            secrets = yaml.safe_load(f)
            pushover_key = secrets.get("pushover_user_key", pushover_key)
            pushover_token = secrets.get("pushover_token", pushover_token)
    if not pushover_key or not pushover_token:
        logger.error(
            "The secrets.yaml file does not exist and/or pushover_key is not provided."
        )
        raise PushoverKeysNotFound(
            "The secrets.yaml file does not exist and/or pushover credentials are not provided."
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
    response = conn.getresponse()
    logger.info(f"Pushover response status: {response.status}")
    if response.status != 200:
        error_message = f"Pushover notification failed: {response.reason}"
        logger.error(error_message)
        raise PushoverNotificationFailed(error_message)
    else:
        logger.info("Pushover notification sent successfully")


def mail(recipient, subj, text, files=None, html=False):
    logger.info("Starting mail function")
    if files is None:
        files = []
    try:
        send_email.send_email(recipient, subj, text, *files, html=html)
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise e


if __name__ == "__main__":
    text = 'Test med html:\n<a href="http://example.com/">word</a>'
    push_notification(text, secrets_file="./input/secrets.yaml")
