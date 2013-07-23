
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy 
import os
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID 
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
app = Flask(__name__)
app.config.from_object('config') #use config.py for web apps
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
#once user is logged in, will go to login page ('/login')
#Flask-login can protext views against non logged in users by added login_requred decorator
lm.login_view = 'login' 
oid = OpenID(app, os.path.join(basedir, 'tmp'))

if not app.debug: #from run.py. Only emails administrator of error if not in debug mode
	import logging
	from logging.handlers import SMTPHandler
	credentials = None
	if MAIL_USERNAME or MAIL_PASSWORD:
		credentials = (MAIL_USERNAME, MAIL_PASSWORD)
	mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'microblog failure', credentials)
	mail_handler.setLevel(logging.ERROR)
	app.logger.addHandler(mail_handler)














from app import views, models

