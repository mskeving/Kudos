#!/usr/bin/python
# From: http://segfault.in/2010/12/sending-gmail-from-python/
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import email_string


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

sender = 'bobmahoney1234@gmail.com'
password = 'norfolkislandpine'
subject = 'Someone sent you kudos!'

def send_email(href, recipient, **kw):
    """
    Sends an email with a button in it

    @param - link - the link that the button takes the user to
    @param - message - the message that the kudos-giver attaches to the post
    @param - recipient - an email address, or comma-separated list of email addresses
    """
    email_body = email_string.gen_email_string(href, **kw)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = recipient
    msg['From'] = sender

    part = MIMEText('text', "html")
    part.set_payload(email_body)
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
    send_email('www.google.com', 'This is a cool message!', recipient)

