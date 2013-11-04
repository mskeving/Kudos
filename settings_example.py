# Copy this to "settings.py" and change the values.

from settings_helper import (
    Settings, AwsCredentials, S3ImageStore, Database, FakeLoginHandler, MailSender,
    base_dir,
    )

import os

data_dir = os.path.join(base_dir, 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
database = Database('sqlite:///' + os.path.join(data_dir, "app.db"))

settings = Settings(
    app_name="Kudos",
    image_store=S3ImageStore(AwsCredentials("access key id", "secret access key"), "s3 bucket name"),
    database=database,
    login_handler=FakeLoginHandler(),
    mail_sender=MailSender(
        server='example.org',
        port=587,
        use_tls=True,
        use_ssl=False,
        username='kudos@example.org',
        password='password',
        reply_to='no-reply-kudos@exmaple.org'),
    admin_emails=['kudos-admin-person@example.org'],
    flask_config=dict(
        CSRF_ENABLED=True,
        SECRET_KEY='you-will-never-guess',
    ))
