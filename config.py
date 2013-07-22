import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True #CROSS-SITE REQUEST FORGERY
SECRET_KEY = 'you-will-never-guess'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#URI is required fy flask-sqlalchemy extension. This is path to database file
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
#folder where we store sqlalchemy migrate data files

OPENID_PROVIDERS = [
    { 'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id' },
    { 'name': 'Yahoo', 'url': 'https://me.yahoo.com' },
    { 'name': 'AOL', 'url': 'http://openid.aol.com/<username>' },
    { 'name': 'Flickr', 'url': 'http://www.flickr.com/<username>' },
    { 'name': 'MyOpenID', 'url': 'https://www.myopenid.com' }]

#mail server settings
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USERNAME = None
MAIL_PASSWORD = None

#administrator list
ADMINS = ['melissaskevington@gmail.com']