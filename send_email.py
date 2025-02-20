import smtplib, ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import platform

os_syst = platform.system()
if os_syst == 'Darwin':
    import keyring

def send_email(receiver_email, subject, text, *files, sender_email="landsverk.vegard@gmail.com",
               keychain_name="Gmail - epostskript (gcal)", pwd_path=".gmail_pwd"):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    size_limit = 25 * 1024 * 1024  # 25MB in bytes

    if os_syst == 'Darwin':  # Macos
        password = keyring.get_password(keychain_name, sender_email)
    elif os_syst == 'Linux':
        with open(pwd_path, "r") as file:
            password = file.read()
    else:
        raise Exception("PasswordNotExists")

    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email


    # Check file sizes and attach files if they are within the size limit
    for f in files or []:
        f = os.path.expanduser(f)
        try:
            file_size = os.path.getsize(f)
            if file_size > size_limit:
                size_in_mb = file_size / (1024 * 1024)
                text += f"\n\nFile '{os.path.basename(f)}' ({size_in_mb:.2f} MB) was not sent due to size limit."
                continue

            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=os.path.basename(f)
                )
        except FileNotFoundError as e:
            raise FileNotFoundError("Invalid file specified.")
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
        message.attach(part)

    # Add the main text to the email
    message.attach(MIMEText(text))

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )

if __name__ == '__main__':
    text = """Hei,
    Her var det jaggu no tekst, ja"
    

    Snakkas!"""
    sub = "Hilsen fra Mons"
    send_email("webansvarlig@skienok.no", sub, text, '~/Downloads/Pipfile')