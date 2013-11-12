import os
import base64
import urllib

from oauth2client.client import (
    FlowExchangeError,
    OAuth2WebServerFlow,
    )

base_dir = os.path.abspath(os.path.dirname(__file__))

class Settings(object):
    def __init__(self,
            app_name,
            image_store,
            database,
            login_handler, 
            mail_sender,
            admin_emails,
            flask_config):
        self.app_name = app_name
        self.image_store = image_store
        self.database = database
        self.login_handler = login_handler
        self.mail_sender = mail_sender
        self.admin_emails = admin_emails
        self.flask_config = flask_config

        self.sqlalchemy_migrations_repo = os.path.join(base_dir, 'db_repository')

class AwsCredentials(object):
    def __init__(self, access_key_id, secret_access_key):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key

class S3ImageStore(object):
    def __init__(self, aws_credentials, bucket_name):
        self.aws_credentials = aws_credentials
        self.bucket_name = bucket_name

class Database(object):
    def __init__(self, url):
        self.url = url

class SqliteDatabase(Database):
    def __init__(self, path):
        parent_dir = os.path.dirname(path)
        if not os.path.exists(parent_dir):
            os.mkdirs(parent_dir)
        super(SqliteDatabase, self).__init__('sqlite:///' + path)

class HerokuDatabase(Database):
    def __init__(self):
        url = os.environ.get('DATABASE_URL')
        if url is None or len(url) == 0:
            raise Exception("Missing environment variable \"DATABASE_URL\".");
        super(HerokuDatabase, self).__init__(url)

class GoogleAuthLoginHandler(object):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def setup(self, app, finish_func):
        from flask import request, redirect, flash, session

        @app.route('/auth_finish')
        def auth_finish():
            code = request.args.get('code')

            csrf_token_and_next = request.args.get('state')
            csrf_token_encoded = csrf_token_and_next.split('|', 1)[0]
            csrf_token = base64.b64decode(csrf_token_encoded)
            next = csrf_token_and_next.split('|', 1)[1]

            #This prevents timing attack rather than using a simple string comparison
            if not safe_string_equals(csrf_token, session['google_auth_csrf']):
                raise Exception("TODO: send 403 page")		

            del session['google_auth_csrf']

            if code:
                try:
                    cred = self.create_auth_flow(request.url_root).step2_exchange(code)
                except FlowExchangeError as e:
                    flash_msg = "An error occured when trying to log in. Please refresh and try again."
                email = cred.id_token.get('email')
                return finish_func(email, next)
            else:
                return finish_func(None, next)

    def start(self, url_root, next):
        from flask import session, render_template
        csrf_token = os.urandom(32)
        session['google_auth_csrf'] = csrf_token
        csrf_token_encoded = base64.b64encode(csrf_token)
        state = csrf_token_encoded + "|" + next
        auth_url = self.create_auth_flow(url_root, state=state).step1_get_authorize_url()
        return auth_url

    def create_auth_flow(self, url_root, **kwargs):
        #TODO: set user_agent - describe all levels of stack
        GOOGLE_API_SCOPE=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
        redirect_uri = url_root + 'auth_finish'

        #to only use dropbox domain, pass hd='dropbox.com'
        #probably don't need to do this because we're checking email in db
        return OAuth2WebServerFlow(client_id=self.client_id, 
                                   client_secret=self.client_secret, 
                                   scope=GOOGLE_API_SCOPE,
                                   redirect_uri=redirect_uri, 
                                   access_type='offline',
                                   **kwargs)

class FakeLoginHandler(object):
    def __init__(self):
        pass

    def setup(self, app, finish_func):
        from flask import request, redirect, flash, render_template
        @app.route('/fake_login')
        def fake_login():
            next = request.args.get('next')
            return render_template('fake_login.html', next=next)

        @app.route('/fake_login_submit', methods=['POST'])
        def fake_login_submit():
            email = request.form.get('email') or ''
            next = request.form.get('next') or None
            print "EMAIL: %r, NEXT: %r" % (email, next)
            return finish_func(email, next)

    def start(self, url_root, next):
        from flask import render_template
        auth_url = '/fake_login'
        if next is not None:
            auth_url += '?next=' + urllib.quote(next)
        return auth_url

class MailSender(object):
    def __init__(self, server, port, use_tls, use_ssl, username, password, reply_to):
        self.server = server
        self.port = port
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.reply_to = reply_to

def safe_string_equals(a, b):
	assert isinstance(a, str), type(a)
	assert isinstance(b, str), type(b)
	if len(a) != len(b):
		return False
	res = 0
	for i in xrange(len(a)):
		res |= ord(a[i]) ^ ord(b[i])
	return res == 0



