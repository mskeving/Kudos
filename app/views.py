import json

from app import app, lm, db, oid
from flask import render_template, flash, redirect, session, url_for, request, g 
from flask.ext.login import login_user, logout_user, current_user, login_required 
from forms import LoginForm, EditForm, EditPost, DeletePost, NewReply
from models import User, Post, UserTeam, Team, Tag, Thanks, ROLE_USER, ROLE_ADMIN
from datetime import datetime
from flask.ext.sqlalchemy import sqlalchemy
from sqlalchemy import and_, or_
from app.lib import email_sender

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

def posts_to_indented_posts(posts):
	# Turns a list of posts from a database query into a list of dictionaries
	# with the right keys/values to be passed to the post.html template
	indented_posts = []

	for p in posts:


		d = {}
		d['post_object'] = p
		d['indent'] = 0

		children = []
		for child in p.children:
			children.append(child)
		d['children_objects'] = children

		tagged_users = []
		tagged_teams = []
		for tag in p.tags:
			if tag.user_tag_id:
				tagged_users.append(tag.user_tag) #send in all user information
			elif tag.team_tag_id:
				tagged_teams.append(tag.team_tag) #just teamname
			else:
				print "no tags for this post.id: %r" % p.id 
		d['tagged_users'] = tagged_users
		d['tagged_teams'] = tagged_teams

		indented_posts.append(d)

	return indented_posts
	

@app.route('/')
@app.route('/index')
@login_required #this page is only seen by logged in users
def index():

	user = g.user
	new_post_form = EditPost() 
	reply_form = NewReply()
	delete_form = DeletePost()
	
	#query for list of available tag words
	user_tags = db.session.query(User).all()
	team_tags = db.session.query(Team).all()
	all_tags = user_tags + team_tags



	tag_dict = {}

	#Available User Tags: full name, last name, nickname, teamname
	for tag in user_tags:
		tag_user_id = "u" + str(tag.id)

		if tag.firstname and tag.lastname and tag.nickname:
			fullname = tag.firstname + " " + tag.lastname + " (" + tag.nickname + ")"
			tag_dict[fullname] = tag_user_id
		elif tag.firstname and tag.lastname:
			fullname = tag.firstname + " " + tag.lastname 
			tag_dict[fullname] = tag_user_id
		elif tag.firstname:
			tag_dict[tag.firstname] = tag_user_id
		elif tag.nickname:
			tag_dict[tag.nickname] = tag_user_id
		else:
			print "no name for user: "


	#Team Tags - all teams
	for tag in team_tags:
		tag_team_id = "t" + str(tag.id)
		tag_dict[tag.teamname] = tag_team_id


	tag_words_string = json.dumps(tag_dict.keys())
	tag_ids_string = json.dumps(tag_dict.values())

	tag_json = json.dumps(tag_dict)


	#query for all parent posts
	posts = Post.query.filter(Post.parent_post_id==None).order_by(Post.time.desc())


	if posts != None:
		indented_posts = posts_to_indented_posts(posts)


	return render_template("index.html", 
		title='Home', 
		user=user,
		posts=indented_posts,
		new_post_form=new_post_form,
		reply_form=reply_form,
		delete_form=delete_form,
		tag_words=tag_words_string,
		tag_ids=tag_ids_string,
		tag_json=tag_json,
		fullname = fullname,

		)

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
	if resp.email is None or resp.email=="":
		flash('Invalid login. Please try again.')
		return redirect(url_for('login'))
	print "EMAIL: %s" % resp.email
	user = User.query.filter_by(email=resp.email).first()
	if user is None:
		flash('You must sign in with Hackbright email address. Please try again.')
		return redirect(url_for('login'))
	remember_me = False 
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me', None) #?
	#register as valid login
	login_user(user, remember=remember_me)
	return redirect(request.args.get('next') or url_for('index'))

@lm.user_loader
def load_user(id):
	#user ids in Flask-login are always unicode. Need to convert to int
	return User.query.get(int(id))

#TEAM PROFILE
@app.route('/team/<team>')
@login_required
def team(team):
 	reply_form = NewReply()
	new_post_form = EditPost()

	print "team: %r" % team

	#team_id is actually teamname, not int
	team_members = UserTeam.query.filter(UserTeam.team_id==team).all()
	team = Team.query.filter_by(teamname=team).first()
	tags = Tag.query.filter(and_(Tag.team_tag_id==team.id, Post.parent_post_id==None)).all() 

	tagged_posts = []
	for tag in tags:
		tagged_posts.append(tag.post)

	indented_posts = []
	if len(tagged_posts) != 0:
		indented_posts = posts_to_indented_posts(tagged_posts)


	list_of_users = []
	for member in team_members:
		list_of_users.append(member.user) #send all user info over

	return render_template('team.html',
		new_post_form=new_post_form,
		reply_form=reply_form,
		team=team.teamname,
		team_members=list_of_users,
		posts=indented_posts,
		)


#USER PROFILE
@app.route('/user/<username>')
@login_required
def user(username):
	reply_form = NewReply()
	new_post_form = EditPost()
	print "username: %r" % username
	user = User.query.filter_by(username=username).first()
	print "user %r " % user
	#user = g.user
	tagged_posts = []
	tags = Tag.query.filter(and_(Tag.user_tag_id==user.id, Post.parent_post_id==None)).all() 
		#get all parent posts that user is tagged in 

	tagged_posts = []
	for tag in tags:
		tagged_posts.append(tag.post)

	indented_posts = []
	if len(tagged_posts) != 0:
		indented_posts = posts_to_indented_posts(tagged_posts)

	dict_of_users_teams = {}

	#TODO: also display tagged posts for the user's teams
	list_of_team_names = []
	teams = db.session.query(UserTeam).filter_by(user_id=user.id).all()
	for team in teams:
		list_of_team_names.append(team.team.teamname)
	dict_of_users_teams[user.id]=list_of_team_names

	print "user's list of teams: "
	print list_of_team_names


	if user == None:
		flash('User ' + username + ' not found.')
		return redirect(url_for('index'))

	print "user before rendering template: %r " % user
	return render_template('user.html', 
		new_post_form=new_post_form,
		reply_form=reply_form,
		user=user, 
		posts=indented_posts,
		list_of_team_names=list_of_team_names,
		)

#EDIT PROFILE
@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.username) #pass in nickname to make sure it's unique
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
		return redirect(url_for('user', username=g.user.username))
	else:
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me

	return render_template('edit.html', 
		form=form, user=g.user)

#ADD NEW POST
@app.route('/editpost', methods=['POST'])
@login_required
def new_post():
	print "in edit post"
	form = request.form
	user_id = g.user.id


	post_text = form.get('post_body')
	if post_text:
		
		new_post = Post(body=post_text, time=datetime.utcnow(), user_id=user_id) 
		db.session.add(new_post)
		db.session.commit()
		db.session.refresh(new_post)


		#Submit tags
		tag_ids = form.get('hidden_tag_ids', '').split('|')
		tag_text = form.get('hidden_tag_text', '').split('|')


		#print "TAG IDS: %s" % tag_ids
		for i in range(len(tag_ids)-1): #last index will be "" because of delimiters 
			#USER TAG
			if tag_ids[i][0] == 'u':
				tag_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
				new_tag = Tag(user_tag_id=tag_id, body=tag_text[i], post_id=new_post.id, tag_author=user_id, time=datetime.utcnow())
				db.session.add(new_tag)
				

				# Get the recipient user, so that we know who to send the email to
				# kudos_recip = User.query.filter(User.id == tag_id).first()

				# #SENDING EMAIL NOTIFICATIONS

				# assert kudos_recip, "Missing kudos recipient"
				# # TODO - Right now, we send an email with:
				# # - A button that links to www.gooogle.com - this should be the permalink of the kudos in future
				# # - To rk@dropbox.com - we should change this to the kudos recipient
				# #print "HEREEEEE\n\n\sdnf\adsnf\asdnf\ansdf\ndasf"
				# #print g.user.email
				# email_sender.send_email(
				# 	url_for('permalink_for_post_with_id', post_id=new_post.id, _external=True),
				# 	'mskeving@gmail.com',
				# 	g.user.email,
				# 	message=post_text,
				# 	sender_name="%s %s" % (g.user.firstname, g.user.lastname)
				# 	)
			#TEAM TAGS
			elif tag_ids[i][0] == 't':
				tag_id = int(tag_ids[i][1:]) #remove leading 't' to convert back to int team_id
				new_tag = Tag(team_tag_id=tag_id, body=tag_text[i], post_id=new_post.id, tag_author=user_id, time=datetime.utcnow())
				db.session.add(new_tag)
		db.session.commit()
		return redirect(url_for('index'))
	else:
		return redirect(url_for('index'))


#SEND THANKS
@app.route('/sendthanks', methods=['POST'])
@login_required
def send_thanks():

	post_id=request.form["post_id"]  
	print "post_id: %r" % post_id

	new_thanks = Thanks(thanks_sender=g.user.id, post_id=post_id, time=datetime.utcnow())
	db.session.add(new_thanks)
	db.session.commit()

	return post_id

#ADD NEW TAG
@app.route('/newtag', methods=['POST'])
@login_required
def add_tag():	
	print "in /newtag"
	user_id = g.user.id
	post_id = request.form["post_id"]

	tag_ids = request.form['tag_ids'].split('|')
	tag_text = request.form['tag_text'].split('|')

	print "tag_ids: %r" % tag_ids
	print "tag_text: %r" % tag_text
 


	new_tag_list={}
	user_tag_info = []
	team_tag_info = []

	for i in range(len(tag_ids)-1): #last index will be "" because of delimiters 
		print "in for loop"
		#USER TAGS
		if tag_ids[i][0] == 'u':
			tag_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
			new_tag = Tag(user_tag_id=tag_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())

			tagged_user = User.query.filter_by(id=tag_id).first()
			user = {}
			user['photo'] = tagged_user.photo
			user['username'] = tagged_user.username
			user_tag_info.append(user)
			db.session.add(new_tag)
		#TEAM TAGS
		if tag_ids[i][0] == 't':
			tag_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
			new_tag = Tag(team_tag_id=tag_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())

			tagged_team = Team.query.filter_by(id=tag_id).first()
			team = {}
			team['photo'] = tagged_team.photo
			team['teamname'] = tagged_team.teamname
			team_tag_info.append(team)
			db.session.add(new_tag)	

	new_tag_list['user_tags'] = user_tag_info	
	new_tag_list['team_tags'] = team_tag_info



	db.session.commit()
	tag_info_json = json.dumps(new_tag_list)
	print "tag_info_json"
	print tag_info_json

	return tag_info_json



#ADD NEW REPLY
@app.route('/newreply', methods=['POST'])
@login_required
def add_reply():
	print "in add_reply"
	reply_form = NewReply()

	#TODO: Validate data
	body = reply_form.reply_body.data
	post_id = request.form['hidden_post_id']
	
	new_reply = Post(body=body, parent_post_id=post_id, time=datetime.utcnow(), user_id=g.user.id)
	db.session.add(new_reply)
	db.session.commit()

	return redirect(url_for('index'))


#DELETE POSTS
@app.route('/deletepost/<postid>', methods=['GET','POST'])
@login_required
def delete_post(postid):
	#post_id = request.form['hidden_post_id'] #hidden value in DeletePost form
	print "in delete post"
	
	delete_post = db.session.query(Post).filter_by(id=postid).one()

	#delete post, replies, associatated tags, and thanks 
	to_delete_list = []
	to_delete_list.append(delete_post)
	for tag in delete_post.tags:
		print tag.id
		to_delete_list.append(tag)
	for child in delete_post.children:
		print child.id
		to_delete_list.append(child)
	for thank in delete_post.thanks:
		print thank.id
		to_delete_list.append(thank)

	for obj_to_delete in to_delete_list: #delete everything associated with post
		print "obj to delete: %r" % obj_to_delete
		db.session.delete(obj_to_delete)

	db.session.commit()

	return redirect(url_for('index'))


@app.route('/post/<post_id>', methods=['GET'])
@login_required
def permalink_for_post_with_id(post_id):
	new_post = EditPost() 
	reply_form = NewReply()
	posts = Post.query.filter(Post.id==int(post_id)).all()
	post = posts_to_indented_posts(posts)[0]

	return render_template('postpage.html',
		user=g.user,
		post=post,
		new_post=new_post,
		reply_form=reply_form,
		)


#ALL USERS
@app.route('/all_users')
@login_required
def all_users():
	all_users = db.session.query(User).all()


	dict_of_users_teams={}
	for user in all_users:
		list_of_teams = []
		teams = db.session.query(UserTeam).filter_by(user_id=user.id).all()
		for team in teams:
			list_of_teams.append(team.team_id)
		dict_of_users_teams[user.id]=list_of_teams


	users_list_of_teams = []
	#users_list_of_teams = db.session.query(Team).filter_by()
	return render_template('allusers.html', 
		all_users=all_users,
		user_teams=dict_of_users_teams,
		)



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
			d['firstname'] = post.dbo.author.firstname
			d['photo'] = post.dbo.author.photo
			d['timestamp'] = post.dbo.time

			posts_list.append(d)
			d = {}
			cls.calcIndentHelper(post.children, posts_list, indent+1)


		return posts_list


		
	@classmethod
	def dump(cls, hposts, indent):
		for post in hposts:
			print indent * " " + str(post.dbo.id), str(post.dbo.body)
			cls.dump(post.children, indent+1)



