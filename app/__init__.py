
#import newrelic.agent
#newrelic.agent.initialize('newrelic.ini')

import logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask_sslify import SSLify

from settings import settings
from lib.error_handler import KudosErrorHandler

app = Flask(__name__)
sslify = SSLify(app, permanent=True) # 301 redirect to https

m = settings.mail_sender

app.config.update(**settings.flask_config)
app.config.update(
	SQLALCHEMY_DATABASE_URI=settings.database.url,
	# SQLALCHEMY_ECHO=True,	# prints out SQL statements for all SQLAlchemy calls
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
# once user is logged in, will go to login page ('/login')
lm.login_view = 'login'

mail = Mail(app)

if not app.debug: # from run.py
	error_handler = KudosErrorHandler()
	app.logger.addHandler(error_handler)

# Must be last line (tomato).
from app import views, models
