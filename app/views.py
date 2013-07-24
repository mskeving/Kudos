from app import app, lm, db, oid
from flask import render_template, flash, redirect, session, url_for, request, g 
from flask.ext.login import login_user, logout_user, current_user, login_required 

from forms import LoginForm, EditForm, EditPost, DeletePost
from models import User, Post, ROLE_USER, ROLE_ADMIN
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

#LOGIN 
@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler #tells Flask-OpenID that this is our login view function
def login():
	if g.user is not None and g.user.is_authenticated():
		#if there's a logged in user already, will not do a second login on top
		return redirect(url_for('index'))
	login_form = LoginForm()

	if login_form.validate_on_submit(): #if anything fails validation, will return false
		#store value of remember_me boolean in flask session (NOT db.session)
		session['remember_me'] = login_form.remember_me.data
		#trigger user authentication through Flask-OpenID
		#form.openid.data is what user enters. nickname and email is the data we want from the openid provider
		return oid.try_login(login_form.openid.data, ask_for = ['nickname', 'email'])
	return render_template('login.html', 
		title = 'Sign In', 
		login_form = login_form,
		providers = app.config['OPENID_PROVIDERS']) #if validation fails, load login page them so they can resubmit 

#LOGOUT
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


#USER PROFILE
@app.route('/user/<nickname>')
@login_required
def user(nickname):

	user = User.query.filter_by(nickname = nickname).first()
	post_form = EditPost()
	if user == None:
		flash('User ' + nickname + ' not found.')
		return redirect(url_for('index'))
	#posts = Post.query.filter_by(id = user.id).all()
	posts = Post.query.filter_by(user_id = user.id).all()
	return render_template('user.html', 
		post_form = post_form,
		user = user, 
		posts = posts)

#EDIT PROFILE
@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.nickname) #pass in nickname to make sure it's unique
		#EditForm is in forms.py
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

#EDIT POSTS
@app.route('/editpost', methods=['POST'])
@login_required
def new_post():
	form = EditPost()

	print form.post_body.name

	#checks if text in form fields
	if form.validate_on_submit():
		# if there's text, submit post
		post_text = form.post_body.data
		user_id = g.user.id
		new_post = Post(body=post_text, timestamp=datetime.utcnow(), user_id=user_id) 
		#don't include id value, primary key will automatically increment
		db.session.add(new_post)
		db.session.commit()
		return redirect(url_for("user", nickname=g.user.nickname))

	else:
		#no text for post. re-render template, which will display error message
		return render_template(('user.html'), post_form=form, user = g.user, posts=g.user.posts)

#DELETE POSTS
@app.route('/deletepost', methods=['POST'])
@login_required
def delete_post():
	form = DeletePost()
	print "created form"
	return render_template(('user.html'), post_form=form, posts=g.user.posts)
	



# @app.errorhandler(404)
# def internal_error(error):
# 	return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_error(error):
# 	db.session.rollback()
# 	return render_template('500.html'), 500
