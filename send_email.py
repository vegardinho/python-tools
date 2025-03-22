import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def send_email(
    receiver_email,
    subject,
    text,
    *files,
    sender_email,
    password,
    html=False,
):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    size_limit = 25 * 1024 * 1024  # 25MB in bytes

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Add the main text to the email
    mime_type = "html" if html else "plain"
    message.attach(MIMEText(text, mime_type))

    # Check file sizes and attach files if they are within the size limit
    if files and files != (None,):
        # Ensure there is a newline before attaching files
        for f in files:
            f = os.path.expanduser(f)
            try:
                file_size = os.path.getsize(f)
                if file_size > size_limit:
                    size_in_mb = file_size / (1024 * 1024)
                    text += f"\n\nFile '{os.path.basename(f)}' ({size_in_mb:.2f} MB) was not sent due to size limit."
                    continue

                with open(f, "rb") as fil:
                    part = MIMEApplication(fil.read(), Name=os.path.basename(f))
            except FileNotFoundError as e:
                raise FileNotFoundError("Invalid file specified.")
            # After the file is closed
            part["Content-Disposition"] = (
                'attachment; filename="%s"' % os.path.basename(f)
            )
            message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


if __name__ == "__main__":
    text = """Hei,
    Her var det jaggu no tekst, ja"
    

    Snakkas!"""
    sub = "Hilsen fra Mons"
    send_email("webansvarlig@skienok.no", sub, text, "~/Downloads/Pipfile")
