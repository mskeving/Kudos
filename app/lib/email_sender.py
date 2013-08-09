# This is from a modified version of http://segfault.in/2010/12/sending-gmail-from-python/
import smtplib

from flask import render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

sender = 'dropbox.kudos@gmail.com'
password = 'wepartyandgivethanks'
subject = 'Someone sent you kudos!'


def gen_email_body(href, **kw):
    """ @param href - the url that the button in the email should take the user to """
    subs = {
        'href': href,
        'message': '',
        'sender_name': 'Someone',
        img_src: '',
    }
    subs.update(kw)
    return render_template('email.html', **subs)


def send_email(href, recipient_email, sender_email, **kw):
    """
    Sends an email with a button in it

    @param - link - the link that the button takes the user to
    @param - message - the message that the kudos-giver attaches to the post
    @param - recipient_email - an email address, or comma-separated string of email addresses
    @param - sender_email - an email address, or comma-separated string of email addresses
    """
    email_body = gen_email_body(href, **kw)

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = recipient_email
    msg['From'] = sender
    msg['Reply-To'] = sender_email

    part = MIMEText('text', "html")
    part.set_payload(email_body)
    msg.attach(part)

    session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    session.ehlo()
    session.starttls()
    session.ehlo
    session.login(sender, password)

    session.sendmail(sender, recipient_email, msg.as_string())
    session.quit()

