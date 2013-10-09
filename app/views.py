import time, os, json, base64, hmac, urllib, hashlib

from base64 import b64encode, b64decode

from app import app, lm, db, mail
from flask import send_from_directory, render_template, flash, redirect, session, url_for, request, g 
from flask.ext.login import (login_user, logout_user, current_user, login_required,
							LoginManager, UserMixin, AnonymousUserMixin, confirm_login, fresh_login_required) 
from oauth2client.client import (FlowExchangeError, flow_from_clientsecrets, OAuth2WebServerFlow)
from forms import LoginForm, EditForm, EditPost, DeletePost, NewReply
from models import User, Post, UserTeam, Team, Tag, Thanks, ROLE_USER, ROLE_ADMIN
from datetime import datetime
from flask.ext.sqlalchemy import sqlalchemy
from sqlalchemy import and_, or_
from app.lib import emails
from emails import follower_notification

from flask.ext.mail import Message




@app.before_request
def before_request():
	#all requests will have access to the logged in user, even in templates
	g.user = current_user
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		

@app.route('/static/img/<path:filename>')
def serve_image(filename):
	image_path = os.path.join(app.root_path, 'static','img')
	return send_from_directory(image_path, filename)



@app.route('/login', methods = ['GET'])
def login():
	#if you're going straight to user profile, and need to login, next parameter makes sure you're redirected to user profile instead of /index
	next = request.args.get('next','')
	csrf_token = os.urandom(32)
	session['google_auth_csrf'] = csrf_token
	csrf_token_encoded = b64encode(csrf_token)
	state = csrf_token_encoded + "|" + next
	auth_uri = create_auth_flow(request, state=state).step1_get_authorize_url()

	return render_template('login.html', 
		title = 'Sign In', 
		auth_uri=auth_uri
        )

@app.route('/auth_finish', methods = ['GET'])
def auth_finish():
	code = request.args.get('code')

	csrf_token_and_next = request.args.get('state')
	csrf_token_encoded = csrf_token_and_next.split('|', 1)[0]
	csrf_token = b64decode(csrf_token_encoded)
	next = csrf_token_and_next.split('|', 1)[1]

	#This prevents timing attack rather than using a simple string comparison
	if not safe_string_equals(csrf_token, session['google_auth_csrf']):
		raise Exception("TODO: send 403 page")		

	del session['google_auth_csrf']

	if code:
		try:
			cred = create_auth_flow(request).step2_exchange(code)

		except FlowExchangeError as e:
			flash_msg = "An error occured when trying to log in. Please refresh and try again."

		#check db to see if email exists for valid users
		u = User.query.filter(User.email==cred.id_token.get('email')).all()
		if len(u) == 0:
			raise Exception('TODO: show error template')
		if len(u) > 1:
			raise Exception('Too many entries in DB for user %r') % cred.id_token.get('email')

		#tell flask to remember that u is current logged in user
		login_user(u[0], remember=True)

	else:
		raise Exception("TODO: error template. You need to authenticate with google to log in.")
	return redirect(next or "/index")


def create_auth_flow(request, **kwargs):
	#TODO: set user_agent - describe all levels of stack
	GOOGLE_API_SCOPE=[
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
	]
	redirect_uri = request.url_root + 'auth_finish'

	#to only use dropbox domain, pass hd='dropbox.com'
	#probably don't need to do this because we're checking email in db
	return OAuth2WebServerFlow(client_id=os.environ.get('GOOGLE_CLIENT_ID'), 
								client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'), 
								scope=GOOGLE_API_SCOPE,
								redirect_uri=redirect_uri, 
								access_type='offline',
								**kwargs)

#LOGOUT
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@lm.user_loader
def load_user(id):
	#user ids in Flask-login are always unicode. Need to convert to int
	return User.query.get(int(id))



@app.route('/')
@app.route('/index')
@login_required #this page is only seen by logged in users
def index():

	#new tags branch

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



#TEAM PROFILE
@app.route('/team/<team>')
@login_required
def team(team):
 	reply_form = NewReply()
	new_post_form = EditPost()

	this_team = Team.query.filter(Team.teamname==team).first()
	team_members = UserTeam.query.filter(UserTeam.team_id==this_team.id).all()
	tags = Tag.query.filter(and_(Tag.team_tag_id==this_team.id, Post.parent_post_id==None)).all() 

	tagged_posts = []
	for tag in tags:
		tagged_posts.append(tag.post)

	indented_posts = []
	if len(tagged_posts) != 0:
		indented_posts = posts_to_indented_posts(tagged_posts)

	dict_of_users_teams = {}
	list_of_users = []
	#get list of teams each member is a part of
	for member in team_members:
		list_of_users.append(member.user)
		list_of_teams = []
		teams = UserTeam.query.filter(UserTeam.user_id==member.user.id).all()
		for team in teams:
			#using DB relationship to get teamname
			list_of_teams.append(team.team.teamname) 
		print "list_of_teams: %r" % list_of_teams
		#keep all user info 
		dict_of_users_teams[member.user] = list_of_teams 

	print "dict_of_users_teams %r" % dict_of_users_teams

	return render_template('team.html',
		new_post_form=new_post_form,
		reply_form=reply_form,
		team=this_team.teamname,
		team_members=list_of_users,
		posts=indented_posts,
		dict_of_users_teams=dict_of_users_teams,
		)


#USER PROFILE
@app.route('/user/<username>')
@login_required
def user(username):
	reply_form = NewReply()
	new_post_form = EditPost()
	user = User.query.filter_by(username=username).first()
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



@app.route('/sign_s3_upload/')
def sign_s3_upload():
	#TODO: Think about preventing abuse of this
	#associate uploads with a user. If there are any things in S3 bucket that aren't referenced with a user, delete them
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')       
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET')

    if app.config['USE_S3']:
    	print "using S3!!!!!"
    print "in sign_s3_upload"

    #TODO: properly quote name in case of spaces or other awkward characters
    # object_name = request.args.get('s3_object_name')

    #create unique filename
    r = os.urandom(32)
    object_name = base64.urlsafe_b64encode(r)+'?x=y&'


    mime_type = request.args.get('s3_object_type')


    expires = int(time.time()+10)
    amz_headers = "x-amz-acl:public-read"

    put_request = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, S3_BUCKET, urllib.quote(object_name))
    print "put_request: %s" % (put_request,)

    #signature generated as SHA1 hash of compiled AWS secret key and PUT request
    signature = base64.encodestring(hmac.new(AWS_SECRET_KEY,put_request, hashlib.sha1).digest())
    print repr(signature)
    #strip surrounding whitespace for safer transmission
    signature = urllib.quote_plus(signature.strip())

    public_url = 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, urllib.quote(object_name))
    print "url: %r " % public_url

    print repr(signature)
    return json.dumps({
        'signed_request': '%s?AWSAccessKeyId=%s&Expires=%d&Signature=%s' % (public_url, AWS_ACCESS_KEY, expires, signature),
         'public_url': public_url
      })


def send_notification(post_id, message, recipient_list, img_url):
	print "in send_notification"
	kudos_header = g.user.firstname + " sent you kudos!"
	recipient_emails = []
	for recipient in recipient_list:
		recipient_emails.append(recipient.email)
	sender = app.config['MAIL_USERNAME']
	recipients=recipient_emails
	print "recipients: %r" % recipients

	msg = Message(subject="You've received a kudos", 
		sender=sender,
		recipients=recipients)

	msg.html = render_template('email.html',
		kudos_header=kudos_header,
		message=message,
		img_url=img_url,
		post_id=post_id,
		)
	

	mail.send(msg)

	return 


#ADD NEW POST
@app.route('/createpost', methods=['POST'])
@login_required
def new_post():

	user_id = g.user.id

	new_post_form = EditPost() 
	reply_form = NewReply()
	delete_form = DeletePost()
	
	form = request.form
	photo_url = form.get('public_url')
	filename = form.get('filename')
	post_text = form.get('post_body')


	if post_text:		
		new_post = Post(body=post_text, time=datetime.utcnow(), user_id=user_id, photo_link=photo_url) 
		db.session.add(new_post)
		db.session.commit()
		db.session.refresh(new_post)
		post_id = new_post.id
	
		#Submit tags
		tag_ids = form.get('hidden_tag_ids', '').split('|')
		tag_text = form.get('hidden_tag_text', '').split('|')

		tagged_user_ids = []
		for i in range(len(tag_ids)-1): #last index will be "" because of delimiters 
			#USER TAG
			if tag_ids[i][0] == 'u':
				user_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
				new_tag = Tag(user_tag_id=user_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())
				tagged_user_ids.append(user_id)
				db.session.add(new_tag)

				
			#TEAM TAGS
			elif tag_ids[i][0] == 't':
				team_id = int(tag_ids[i][1:]) #remove leading 't' to convert back to int team_id
				new_tag = Tag(team_tag_id=team_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())
				db.session.add(new_tag)
		db.session.commit()

		
		db.session.refresh(new_post)
		posts=[new_post,]
		indented_post = posts_to_indented_posts(posts)[0]

		#Send email notification to taggees that they've been tagged in a post
		tagged_users = User.query.filter(User.id.in_(tagged_user_ids))
		send_notification(post_id, post_text, tagged_users, photo_url)


		post_page = render_template('post.html', 
			post=indented_post, 
			reply_form=reply_form,
			new_post_form=new_post_form,
			)

		return post_page
	else:
		return "There needs to be text to submit a new post"

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

#REMOVE THANKS
@app.route('/removethanks', methods=['POST'])
@login_required
def remove_thanks():
	form = request.form

	thanks_sender = g.user.id
	post_id = form.get('post_id')

	delete_thanks = Thanks.query.filter(and_(Thanks.thanks_sender==thanks_sender, Thanks.post_id==post_id)).all() 

	for thank in delete_thanks:
		db.session.delete(thank)
	db.session.commit()

	status = "complete"
	return status


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
 


	new_tag_dict={}
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
			user['user_id'] = tagged_user.id
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
			team['team_id'] = tagged_team.id
			team_tag_info.append(team)
			db.session.add(new_tag)	

	new_tag_dict['user_tags'] = user_tag_info	
	new_tag_dict['team_tags'] = team_tag_info



	db.session.commit()
	tag_info_json = json.dumps(new_tag_dict)

	return tag_info_json

#DELETE TAGS
@app.route('/deletetag/<tagid>', methods=['GET','POST'])
@login_required
def delete_tag(tagid):
	
	delete_tag = db.session.query(Tag).filter_by(id=tagid).one()

	db.session.delete(delete_tag)
	db.session.commit()

	status = "complete"

	return status


#ADD NEW COMMENT
@app.route('/newcomment', methods=['POST'])
@login_required
def new_comment():

	form = request.form

	body = form.get('body')
	post_id = form.get('post_id')
	
	print "post_id: %r" % post_id

	new_comment = Post(body=body, parent_post_id=post_id, time=datetime.utcnow(), user_id=g.user.id)
	db.session.add(new_comment)
	db.session.commit()

	comment_info = {}
	comment_info["comment_id"] = new_comment.id
	comment_info["author_username"] = new_comment.author.username
	comment_info["author_photo"] = str(new_comment.author.photo)

	if new_comment.author.firstname and new_comment.author.lastname: 
		comment_info["author_name"] = new_comment.author.firstname + " " + new_comment.author.lastname
	elif new_comment.author.firstname:
		comment_info["author_name"] = new_comment.author.firstname
	else:
		comment_info["author_name"] = new_comment.author.username

	comment_info_json = json.dumps(comment_info)

	return comment_info_json

#DELETE COMMENT
@app.route('/deletecomment/<postid>', methods=['POST'])
@login_required
def delete_comment(postid):
	
	delete_comment = db.session.query(Post).filter_by(id=postid).one()
	db.session.delete(delete_comment)
	db.session.commit()

	status = "complete"

	return status


#DELETE POSTS
@app.route('/deletepost/<postid>', methods=['GET','POST'])
@login_required
def delete_post(postid):
	form = request.form


	
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


	return postid

	return redirect(url_for('index'))



#POST PAGE
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


def safe_string_equals(a, b):
    assert isinstance(a, str), type(a)
    assert isinstance(b, str), type(b)
    if len(a) != len(b):
        return False
    res = 0
    for i in xrange(len(a)):
        res |= ord(a[i]) ^ ord(b[i])
    return res == 0


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
				tagged_users.append(tag) #send in all user information
			elif tag.team_tag_id:
				tagged_teams.append(tag) #just teamname
			else:
				print "no tags for this post.id: %r" % p.id 
		d['tagged_users'] = tagged_users
		d['tagged_teams'] = tagged_teams

		#list of users giving thanks for post
		thanks_senders = []
		for thank in p.thanks:
			thanks_senders.append(thank.user.username)
		d['thanks_senders'] = thanks_senders

		indented_posts.append(d)

	return indented_posts
	

