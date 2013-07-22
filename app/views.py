from app import app, lm, db, oid
from flask import render_template, flash, redirect, session, url_for, request, g 
from flask.ext.login import login_user, logout_user, current_user, login_required 

from forms import LoginForm, EditForm
from models import User, ROLE_USER, ROLE_ADMIN
from datetime import datetime

@app.before_request
def before_request():
	#all requests will have access to the logged in user, even in templates
	g.user = current_user
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()

@app.route('/')
@app.route('/index')
@login_required #this page is only seen by logged in users
def index():
	user = g.user
	posts = [
		{
			'author':{'nickname':'John'},
			'body': 'Beautiful day in Portland!'
		}, 
		{
			'author':{'nickname':'Susan'},
			'body':'The Avengers was a good movie.'
		}

	]
	return render_template("index.html", 
		title = 'Home', 
		user = user, 
		posts = posts)

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler #tells Flask-OpenID that this is our login view function
def login():
	if g.user is not None and g.user.is_authenticated():
		#if there's a logged in user already, will not do a second login on top
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit(): #if anything fails validation, will return false
		#store value of remember_me boolean in flask session (NOT db.session)
		session['remember_me'] = form.remember_me.data
		#trigger user authentication through Flask-OpenID
		#form.openid.data is what user enters. nickname and email is the data we want from the openid provider
		return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
	return render_template('login.html', 
		title = 'Sign In', 
		form = form,
		providers = app.config['OPENID_PROVIDERS']) #if validation fails, load login page them so they can resubmit 

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@oid.after_login
#resp has info returned by OpenID provider
def after_login(resp):
	if resp.email is None or resp.email == "":
		flash('Invalid login. Please try again.')
		return redirect(url_for('login'))
	user = User.query.filter_by(email = resp.email).first()
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
		db.session.add(user)
		db.session.commit()
	remember_me = False 
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None) #?
	#register as valid login
	login_user(user, remember = remember_me)
	return redirect(request.args.get('next') or url_for('index'))

@lm.user_loader
def load_user(id):
	#user ids in Flask-login are always unicode. Need to convert to int
	return User.query.get(int(id))

@app.route('/user/<nickname>')
@login_required
def user(nickname):
	user = User.query.filter_by(nickname = nickname).first()
	if user == None:
		flash('User ' + nickname + ' not found.')
		return redirect(url_for('index'))
	posts = [
		{ 'author': user, 'body': 'Test post #1' },
		{ 'author': user, 'body': 'Test post #2'}
	]
	return render_template('user.html', 
		user = user, 
		posts = posts)

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm()
	if form.validate_on_submit():
		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash('Your changes have been saved')
		return redirect(url_for('edit'))
	else:
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
	return render_template('edit.html', 
		form = form)

@app.errorhandler(404)
def internal_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500
