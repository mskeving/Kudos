import json

from app import app, lm, db, oid
from flask import render_template, flash, redirect, session, url_for, request, g 
from flask.ext.login import login_user, logout_user, current_user, login_required 

from forms import LoginForm, EditForm, EditPost, DeletePost, NewReply
from models import User, Post, UserTeam, Team, Tag, ROLE_USER, ROLE_ADMIN
from datetime import datetime

@app.before_request
def before_request():
	#all requests will have access to the logged in user, even in templates
	g.user = current_user
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		

@app.route('/nothing', methods = ['GET', 'POST'])
def nothing():
	print "in nothing"
	return "True"

@app.route('/')
@app.route('/index')
@login_required #this page is only seen by logged in users
def index():

	user = g.user
	posts = Post.query.all()

	user_tags = db.session.query(User).all()
	#team_tags = db.session.query(User).filter(User.team != None).all()
	team_tags = db.session.query(Team).all()
	all_tags = user_tags + team_tags



	#create list of tag words
	#then pass list of JSON tag objects
	#all_tag_info = json.dumps(all_tags) <-- error: json object not iterable

	tag_dict = {}


	#Available Tags: full name, last name, nickname, teamname
	for tag in user_tags:
		tag_user_id = "u" + str(tag.id)
		if tag.firstname and tag.lastname and tag.nickname:
			fullname = tag.firstname + " " + tag.lastname + " (" + tag.nickname + ")"
			tag_dict[tag_user_id] = fullname
		elif tag.firstname and tag.lastname:
			fullname = tag.firstname + " " + tag.lastname 
			tag_dict[tag_user_id] = fullname
		elif tag.firstname:
			tag_dict[tag_user_id] = tag.firstname
			
		else:
			print "no name for user: "


	for tag in team_tags:
		tag_team_id = "t" + str(tag.id)
		tag_dict[tag_team_id] = tag.teamname


	tag_words = tag_dict.values()
	tag_ids = tag_dict.keys()

	tagstring = json.dumps(tag_words)
	tag_ids_string = json.dumps(tag_ids)


	new_post = EditPost() 
	reply_form = NewReply()

	#CREATE POST TREE
	indented_posts=[]
	if posts != None:
		#create parent/child list of all posts
		hposts = HPost.build(posts)
		#indentend posts = list of (post body, indent) values
		indented_posts = HPost.calcIndent(hposts)

		#for debugging
		#HPost.dump(hposts,0)

	return render_template("index.html", 
		title='Home', 
		user=user,
		posts=indented_posts,
		new_post=new_post,
		reply_form=reply_form,
		tags=tagstring,
		tag_ids=tag_ids_string,
		fullname = fullname)


#LOGIN 
@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler #tells Flask-OpenID that this is our login view function
def login():
	#return str(request.args['openid_complete'])
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
        ) #if validation fails, load login page them so they can resubmit 



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
		flash('You must sign in with your @dropbox email address. Please try again.')
		return redirect(url_for('login'))
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

#TEAM PROFILE
@app.route('/team/<team>')
@login_required
def team(team):
	team_members = User.query.filter_by(team = team).all()
	print "team: " + team
	print "team members: "
	print team_members

	return render_template('team.html',
		team = team,
		team_members = team_members)


#USER PROFILE
@app.route('/user/<nickname>')
@login_required
def user(nickname):

	user = User.query.filter_by(nickname = nickname).first()
	posts = Post.query.filter_by(user_id = user.id).all()

	edit_form = EditPost()
	delete_form = DeletePost()

	if user == None:
		flash('User ' + nickname + ' not found.')
		return redirect(url_for('index'))

	#CREATE POST TREE
	indented_posts=[]
	if posts != None:
		#create parent/child list of all posts
		hposts = HPost.build(posts)
		#indentend posts = list of (post body, indent) values
		indented_posts = HPost.calcIndent(hposts)

		#for debugging
		#HPost.dump(hposts,0)

	print "user before render_template: " + str(user)
	return render_template('user.html', 
		edit_form = edit_form,
		delete_form = delete_form,
		user = user, 
		posts = indented_posts)

#EDIT PROFILE
@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.nickname) #pass in nickname to make sure it's unique
		#EditForm is in forms.py
	if form.validate_on_submit():
		#is there a more succinct way of doing this? Looping through form elements?
		g.user.nickname = form.nickname.data
		g.user.firstname = form.firstname.data
		g.user.lastname = form.lastname.data
		g.user.team = form.team.data
		g.user.email = form.email.data
		g.user.phone = form.phone.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		return redirect(url_for('user', nickname=g.user.nickname))
	else:
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me

	return render_template('edit.html', 
		form=form, user=g.user)

#ADD NEW POST
@app.route('/editpost', methods=['POST'])
@login_required
def new_post():
	#TODO: commit everything (posts and tags) at end
	form = EditPost()
	user_id = g.user.id


	#checks if new Post
	if form.validate_on_submit():
		# if there's text, submit post
		post_text = form.post_body.data
		
		new_post = Post(body=post_text, timestamp=datetime.utcnow(), user_id=user_id) 
		db.session.add(new_post)
		db.session.commit()
	

		#Submit tags
		print "hidden data: "
		print form.hidden_tag_ids.data
		tag_ids = form.hidden_tag_ids.data.split('|')
		tag_text = form.hidden_tag_text.data.split('|')

		print tag_text


		for i in range(len(tag_ids)-1): #last index will be "" because of delimiters 
			if tag_ids[i][0] == 'u':
				tag_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
				new_tag = Tag(user_tag_id=tag_id, body=tag_text[i], post_id=new_post.id, tag_author=user_id, timestamp = datetime.utcnow())
				db.session.add(new_tag)
				db.session.commit()
			elif tag_ids[i][0] == 't':
				tag_id = int(tag_ids[i][1:]) #remove leading 't' to convert back to int team_id
				new_tag = Tag(team_tag_id=tag_id, body=tag_text[i], post_id=new_post.id, tag_author=user_id, timestamp = datetime.utcnow())
				db.session.add(new_tag)
				db.session.commit()


		return redirect(url_for('index'))

	else:
		#no text for post. display error message??
		return redirect(url_for('index'))



#ADD NEW REPLY
@app.route('/newreply', methods=['POST'])
@login_required
def add_reply():
	print "in add_reply"
	reply_form = NewReply()

	print "body: " + reply_form.reply_body.data
	#if reply_form.validate_on_submit():
	body = reply_form.reply_body.data
	print "body: " + body
	post_id = request.form['hidden_post_id']
	
	new_reply = Post(body = body, parent_post_id = post_id, timestamp = datetime.utcnow(), user_id = g.user.id)
	print str(new_reply) + " ready to be added"
	db.session.add(new_reply)
	db.session.commit()

	return redirect(url_for('index'))
	# else:
	# 	print "not validated"
	# 	return redirect(url_for('index'))
		#add redirect to include error message that no text was included

#DELETE POSTS
@app.route('/deletepost', methods=['POST'])
@login_required
def delete_post():
	print "in /deletepost"
	form = DeletePost()

	post_id = request.form['hidden_post_id'] #hidden value in DeletePost form
	user_id = g.user.id

	delete_post = db.session.query(Post).filter_by(id=post_id).one()

	db.session.delete(delete_post)
	db.session.commit()
	print "committed to database"
	return redirect(url_for('user', nickname=g.user.nickname))



#ALL USERS
@app.route('/all_users')
@login_required
def all_users():
	all_users = db.session.query(User).all()
	return render_template('allusers.html', all_users=all_users)



# @app.errorhandler(404)
# def internal_error(error):
# 	return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_error(error):
# 	db.session.rollback()
# 	return render_template('500.html'), 500


class HPost:
	def __init__(self, dbo):
		self.dbo = dbo
		self.children = []

	#the representation 
	def __repr__(self):
		return "HPost(%d, %r)" % (self.dbo.id, self.children)

	@staticmethod
	def build(posts_list):
		#builds a tree of all posts
		#returns lists of parent post, with list of replies 
		#Each parent creates a new HPost, with post_id as dbo and children is list of replies
		#HPost(1, [HPost(3)]) -- 3rd post in Post is reply to first post

		ret = []
		d = {}
		for post in posts_list:
			h = HPost(post)
			d[post.id] = h

			#parent posts have no parent_post_id
			if post.parent_post_id == None:
				
				ret.append(h)
			#if it's a child, append to parent's children list
			else:
				parent = post.parent_post_id	
				d[parent].children.append(h)
		return ret


	#create empty list to append to in calcIndentHelper
	@staticmethod
	def calcIndent(hposts):
		posts_list = []
		posts_list = HPost.calcIndentHelper(hposts, posts_list)
		return posts_list


	#cls is HPost, so you can do cls.method instead of HPost.method
	@classmethod
	def calcIndentHelper(cls, hposts, posts_list, indent=0):
		#returns a list of dictionaries. Each dictionary has properties of each post

		d = {}
		for post in hposts:
			#better way of getting column names? 
			d['body'] = post.dbo.body
			d['indent'] = indent
			d['post_id'] = post.dbo.id
			d['nickname'] = post.dbo.author.nickname
			d['timestamp'] = post.dbo.timestamp

			posts_list.append(d)
			d = {}
			cls.calcIndentHelper(post.children, posts_list, indent+1)


		return posts_list


		
	@classmethod
	def dump(cls, hposts, indent):
		for post in hposts:
			print indent * " " + str(post.dbo.id), str(post.dbo.body)
			cls.dump(post.children, indent+1)



