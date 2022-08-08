import http.client, urllib
import send_email


def push_notification(text, pushover_token):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
     urllib.parse.urlencode({
         "token": pushover_token,
         "user": "uvieox1v1tdsubdnmipw4igx1u65xj",
         "message": text,
         "html": 1, #Enable html formatting
     }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


def mail(recipient, subj, text):
    send_email.send_email("landsverk.vegard@gmail.com", recipient,
                          "Gmail - epostskript (gcal)", subj, text)


if __name__ == '__main__':
    text = "Test med html:\n<a href=\"http://example.com/\">word</a>"
    push_notification(text)