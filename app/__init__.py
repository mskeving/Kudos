
#import newrelic.agent
#newrelic.agent.initialize('newrelic.ini')

import logging.handlers
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy 
import os
from flask.ext.login import LoginManager
from flask.ext.mail import Mail

from settings import settings

app = Flask(__name__)

m = settings.mail_sender

app.config.update(**settings.flask_config)
app.config.update(
	SQLALCHEMY_DATABASE_URI=settings.database.url,
	SQLALCHEMY_ECHO=True,
	MAIL_SERVER=m.server,
	MAIL_PORT=m.port,
	MAIL_USERNAME=m.username,
	MAIL_PASSWORD=m.password,
	MAIL_USE_TLS=m.use_tls,
	MAIL_USE_SSL=m.use_ssl,
	DEFAULT_MAIL_SENDER=m.username,
	)
app.jinja_env.add_extension('jinja2.ext.do')

db = SQLAlchemy(app)
lm = LoginManager()
lm.login_message = None
lm.init_app(app)
#once user is logged in, will go to login page ('/login')
#Flask-login can protect views against non logged in users by added login_requred decorator
lm.login_view = 'login' 

mail = Mail(app)

if not app.debug: #from run.py. Only emails administrator of error if not in debug mode
    credentials = None
    if m.username or m.password:
        credentials = (m.username, m.password)
    mail_handler = logging.handlers.SMTPHandler(
            (m.server, m.port),
            m.reply_to, settings.admin_emails, 'Missy failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    #app.logger.addHandler(mail_handler)

# Must be last line (tomato).
from app import views, models
