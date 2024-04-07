import keyring
import smtplib, ssl
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os


def send_email(receiver_email, subject, text, *files, sender_email="landsverk.vegard@gmail.com",
               keychain_name="Gmail - epostskript (gcal)"):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    password = keyring.get_password(keychain_name, sender_email)
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Turn these into plain/html MIMEText objects
    # plain_text = MIMEText(text, "plain")
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    # message.attach(plain_text)
    message.attach(MIMEText(text))

    for f in files or []:
        f = os.path.expanduser(f)
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        message.attach(part)
    
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )

if __name__ == '__main__':
    text = """Hei,
	Her var det jaggu no tekst, ja"
	

	Snakkas!"""
    sub = "Hilsen fra Mons"
    send_email("webansvarlig@skienok.no", sub, text, '~/Downloads/unnamed.png')
