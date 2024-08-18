import http.client, urllib
import send_email


def push_notification(text, pushover_token, pushover_key):
    if pushover_key == None:
        pushover_key = "uvieox1v1tdsubdnmipw4igx1u65xj"

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
     urllib.parse.urlencode({
         "token": pushover_token,
         "user": pushover_key,
         "message": text,
         "html": 1, #Enable html formatting
     }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


def mail(recipient, subj, text, files=None):
    send_email.send_email(recipient, subj, text, files)


if __name__ == '__main__':
    text = "Test med html:\n<a href=\"http://example.com/\">word</a>"
    push_notification(text)