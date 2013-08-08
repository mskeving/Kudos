#!/usr/bin/python
# From: http://segfault.in/2010/12/sending-gmail-from-python/
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

sender = 'bobmahoney1234@gmail.com'
password = 'norfolkislandpine'
subject = 'Someone sent you kudos!'
message = """
<html>
    <body>
        <div class="container" style="background-color: #4688f1; color: white; border-radius: 3px; padding: 15px; text-align: center;">

            <div class="kudos header" style="font-size: 25px;">
                Someone sent you Kudos...
            </div>

            <div class="kudos message" style="width: 320px; margin: 15px auto auto auto; color: white;">
                Soleio is a cool guy! He will make this email look way more awesome than it is right now.
                At the very least, it is currently way too blue and the font is the default ugly GMail font.
            </div>
    </body>
</html>
"""

def send_email_to(recipient):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = recipient
    msg['From'] = sender

    part = MIMEText('text', "html")
    part.set_payload(message)
    msg.attach(part)

    session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    session.ehlo()
    session.starttls()
    session.ehlo
    session.login(sender, password)

    session.sendmail(sender, recipient, msg.as_string())
    session.quit()

if __name__ == '__main__':
    recipient = 'rk@dropbox.com, mskeving@gmail.com'
    send_email_to(recipient)

