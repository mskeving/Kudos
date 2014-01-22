import time, os, json, base64, hmac, urllib, hashlib, random
from collections import defaultdict
from base64 import b64encode, b64decode
from settings import settings

from app import app, lm, db, mail
from flask import (send_from_directory, render_template, flash,
				redirect, session, url_for, request, g, current_app)
from flask.ext.login import (login_user, logout_user, current_user,
							login_required,	LoginManager, UserMixin,
							AnonymousUserMixin, confirm_login,
							fresh_login_required)
from oauth2client.client import (FlowExchangeError,
								OAuth2WebServerFlow)
from forms import EditPost
from models import (User, Post, UserTeam, Team, Tag,
					Thanks, UNMODERATED, ACCEPTED, REJECTED)
from datetime import datetime
from flask.ext.sqlalchemy import sqlalchemy
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload_all
from threading import Thread

from flask.ext.mail import Message

from settings import settings

def auth_finish(email, next):
	if email is None:
		error_msg = "You need to authenticate with Google in order to log in to Kudos."
		return back_to_login_with_error(error_msg)

	#check db to see if email exists for valid users
	u = User.query.filter(User.email==email).all()

	def back_to_login_with_error(error_msg):
		flash(error_msg)
		return redirect(url_for('login'))

	if len(u) == 0:
		error_msg = "You're not registered on Dropbox Kudos yet - are you a new Dropboxer? If so, contact kudos@dropbox.com to get access."
		return back_to_login_with_error(error_msg)

	if len(u) > 1:
		error_msg = "Too many entries for %r in database. Please contact kudos@dropbox.com" % cred.id_token.get('email')
		return back_to_login_with_error(error_msg)

	if u[0].is_deleted == True:
		error_msg = "Looks like you no longer have access to Dropbox Kudos. If you think this is in error, contact kudos@dropbox.com to get access."
		return back_to_login_with_error(error_msg)

	#tell flask to remember that u is current logged in user
	login_user(u[0], remember=True)

	return redirect(next or '/')

settings.login_handler.setup(app, auth_finish)

# g.user is User object of the logged in user. All requests will have access to this.
@app.before_request
def before_request():
	g.user = current_user

# for avatars when no S3 connection - not currently in use.
@app.route('/static/img/<path:filename>')
def serve_image(filename):
	image_path = os.path.join(app.root_path, 'static','img')
	return send_from_directory(image_path, filename)


@app.route('/login', methods = ['GET'])
def login():
	next = request.args.get('next','')  # 'next' is where to go after login is complete.
	auth_url = settings.login_handler.start(request.url_root, next)
	return render_template('login.html', auth_url=auth_url)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))

@lm.user_loader
def load_user(id_str):
	# TODO: Flask-Login calls load_user even on static routes.
	# - Fixing with a cache could be tricky (consistency, multithreading)
	# - Fixing by returning None for static routes doesn't work, because returning None
	#   clears the login cookie.
	return User.query.get(int(id_str))

@app.route('/feedback', methods=['POST'])
@login_required
def feedback():
	form = request.form

	sender = g.user.email
	reply_to = sender
	recipient_list = ["kudos@dropbox.com"]
	subject = "Kudos Feedback"
	text = form.get('feedback')

	kudos_header = "feedback from %s %s" %(g.user.firstname, g.user.lastname)
	html = render_template('feedback_email.html',
		text=text,
		kudos_header=kudos_header,
	)
	post_id = None
	send_email(sender, recipient_list, reply_to, subject, html, post_id)

	return "complete"


@app.route('/')
@app.route('/index')
@login_required
def index():
	'''
	Home page - displays most recent 10 posts and a post-modal to submit new posts.
	returns:
		- index.html
	'''

	user = g.user
	new_post_form = EditPost()

	#query for all parent posts
	posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False)).order_by(Post.time.desc()).limit(10).all()

	if posts != None:
		indented_posts = posts_to_indented_posts(posts)

	return render_template("index.html",
		title='Home',
		user=user,
		posts=indented_posts,
		new_post_form=new_post_form,
	)


@app.route('/tv')
def tv():
	'''
	endpoint to fetch posts for display page (most recent 10 posts).
	Will only display posts that have been accepted by an admin

	returns:
		- tv-display.html
	'''
	#query for all parent posts
	posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.status==ACCEPTED)).order_by(Post.time.desc()).limit(10).all()

	if posts != None:
		indented_posts = posts_to_indented_posts(posts)

	return render_template("tv-display.html",
		posts=indented_posts,
	)


def admin_required(f):
	'''
	decorator for pages only admins can see
	admins are defined in settings.py under admin_emails
	'''
	from functools import wraps
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if g.user.email not in settings.admin_emails:
			return render_template('error_page.html',
				error_msg="This page is only available to Kudos admins")
		return f(*args, **kwargs)
	return decorated_function



@app.route('/admin')
@app.route('/admin/unmoderated')
@login_required
@admin_required
def unmoderated_posts():
	'''
	Use /admin to determine which posts are display on TV
	no link currently goes to this endpoint. Will need to type /admin manually
	Defaults to showing all unmoderated posts, waiting to be accepted or rejected

	returns:
		- call to render_admin_page
	'''
	# UNMODERATED = 0
	status = UNMODERATED
	header = 'Unmoderated Posts: '
	return render_admin_page(status, header)


@app.route('/admin/accepted')
@login_required
@admin_required
def accepted_posts():
	# ACCEPTED = 1
	status = ACCEPTED
	header = 'Accepted Posts: '
	return render_admin_page(status, header)

@app.route('/admin/rejected')
@login_required
@admin_required
def rejected_posts():
	# REJECTED = 2
	status = REJECTED
	header = 'Rejected Posts: '
	return render_admin_page(status, header)


def render_admin_page(status, header):
	'''
	Queries for all posts with given status
	Then does a separate query for each status individually to get counts for each category
	TODO: be smarter about this flow.

	Args:
		- status: could be ACCEPTED, REJECTED, or UNMODERATED
		- header: used in admin.html to ittle the list of posts ex. 'Rejected Posts: '

	Returns:
		- admin.html
	'''
	user = g.user
	new_post_form = EditPost()

	posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.status==status)).order_by(Post.time.desc()).all()

	accepted_posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.status==ACCEPTED)).all()
	rejected_posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.status==REJECTED)).all()
	unmoderated_posts = Post.query.filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.status==UNMODERATED)).all()
	count_accepted_posts = len(accepted_posts)
	count_rejected_posts = len(rejected_posts)
	count_unmoderated_posts = len(unmoderated_posts)

	if posts is not None:
		indented_posts = posts_to_indented_posts(posts)

	# reassign status to string to use in template logic for readability
	if status == REJECTED:
		status = 'rejected'
	elif status == ACCEPTED:
		status = 'accepted'
	else:
		status = 'unmoderated'

	return render_template('admin.html',
		title='admin',
		user=user,
		header=header,
		posts=indented_posts,
		new_post_form=new_post_form,
		status=status,
		count_unmoderated_posts=count_unmoderated_posts,
		count_accepted_posts=count_accepted_posts,
		count_rejected_posts=count_rejected_posts,
	)


@app.route('/moderate_post', methods=['POST'])
@login_required
def moderate_post():
	'''
	Called when admin clicks on 'accept' or 'reject' for given post
	Changes status value in db for that post

	Args (from ajax request):
		- post_id: post id for parent post being moderated
		- status: 1 or 2 depending on if it's accepted or rejected respectively

	Returns:
		- 'complete'
	'''
	form = request.form
	post_id = form.get('post_id')
	status = form.get('status')

	post = Post.query.filter(Post.id==post_id).one()

	post.status = int(status)
	post.status_committer = g.user.email

	db.session.commit()

	return "complete"


@app.route('/get_more_posts', methods=['POST'])
@login_required
def get_more_posts():
	'''
	Endpoint for infinite scrolling function located in index.js
	Fetches the next 5 posts

	Args (from ajax request):
		- last_post_id: post id of last post currently displayed on page

	Returns:
		- json of post.html for each new post to display
	'''

	new_post_form = EditPost()
	form = request.form
	num_posts_to_display = 5

	last_post_id = form.get('last_post_id')

	if last_post_id:
		#older posts will have smaller post_id
		total_posts_left = db.session.query(Post).filter(and_(Post.parent_post_id==None, Post.is_deleted==False, Post.id<last_post_id)).all()
	else:
		total_posts_left = []

	posts_to_display = []
	count_total_posts_left = len(total_posts_left)
	#next posts to display are at end of list
	for post in total_posts_left[-1:-num_posts_to_display:-1]:
		posts_to_display.append(post)

	indented_posts = []
	if len(posts_to_display) > 0:
		indented_posts = posts_to_indented_posts(posts_to_display)

	new_posts = ""
	for post in indented_posts:
		new_posts += render_template('post.html',
			post=post,
			new_post_form=new_post_form,
		)

	new_posts_json = json.dumps(new_posts)

	return new_posts_json



@app.route('/create_tag_list', methods=['POST'])
@login_required
def create_tag_list():
	'''
	Called each time you interact with tag tokenizer
	Queries for all potential tags (users and teams) and excludes those already used on post
	'u' and 't' are prepend to user and team tags respectively to differentiate id's

	Args (from ajax request):
		- post_id: post id of post to get potential tags for

	Returns:
		- json of all available tags (includes user/team id's and name strings)
	'''

	form = request.form
	post_id = form.get('post_id')

	user_tags = User.query.filter_by(is_deleted=False).all()
	team_tags = Team.query.filter_by(is_deleted=False).all()
	all_tags = user_tags + team_tags

	# Can never tag yourself
	used_tags_dict = {
		g.user.id: 'user'
	}

	if post_id:
		#query for tags already associated with given post
		#there won't be a post_id if you're getting tag list to submit new post
		used_tags = Tag.query.filter(Tag.post_id==post_id).all()
		for used_tag in used_tags:
			if used_tag.team_tag_id:
				used_tags_dict[used_tag.team_tag_id] = 'team'
			else:
				used_tags_dict[used_tag.user_tag_id] = 'user'
		print "used_tags_dict: %r " % used_tags_dict

	tag_dict = {}
	# will include all available tags for given post
	# {name: user_id,
	#	teamname: team_id}

	for tag in user_tags:
		if tag.id in used_tags_dict:
			#if tag has already been used on this post, don't add to available tags
			continue

		# prepend 'u' to denote it's a user tag, and keep id unqiue from team id's
		tag_user_id = "u" + str(tag.id)
		#Available User Tags: full name, last name, nickname, teamname
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


	for tag in team_tags:
		if tag.id in used_tags_dict:
			continue
		# prepend 't' to keep id's unique from user id's
		tag_team_id = "t" + str(tag.id)
		tag_dict[tag.teamname] = tag_team_id


	tag_words_string = tag_dict.keys()
	tag_ids_string = tag_dict.values()

	return json.dumps({'tag_words': tag_words_string,
		'tag_ids': tag_ids_string,
		'tag_dict': tag_dict
	})


@app.route('/team/<team>')
@login_required
def team(team):

	'''
	Team Profile: Displays all teams members for given team
	Displays all posts where given team is tagged in

	Returns:
		- team.html
	'''
	new_post_form = EditPost()

	this_team = Team.query.filter(Team.teamname==team).first()
	name = "the " + this_team.teamname + " Team"
	team_members = UserTeam.query.filter(UserTeam.team_id==this_team.id).all()
	tags = Tag.query.filter(and_(Tag.team_tag_id==this_team.id, Tag.is_deleted==False)).order_by(Tag.time.desc()).all()

	tagged_posts = [tag.post for tag in tags]

	#comment
	if len(tagged_posts) != 0:
		indented_posts = [posts_to_indented_posts(tagged_posts)]

	dict_of_users_teams = {}
	list_of_users = []
	# get list of teams each member is a part of (a user can be on multiple teams)
	# info not currently used on team.html
	for member in team_members:
		list_of_users.append(member.user)
		list_of_teams = []
		teams = UserTeam.query.filter(UserTeam.user_id==member.user.id).all()
		for team in teams:
			#using DB relationship to get teamname
			list_of_teams.append(team.team.teamname)
		dict_of_users_teams[member.user] = list_of_teams

	# Needed so new posts will automatically tag given team
	prefill_data = {
		'id': 't' + str(this_team.id), # prepend with 't' to differentiate from user id's
		'name': this_team.teamname,
	}

	return render_template('team.html',
		new_post_form=new_post_form,
		team=this_team,
		team_members=list_of_users,
		posts=indented_posts,
		dict_of_users_teams=dict_of_users_teams,
		name=name,
		prefill_data=prefill_data,
	)



@app.route('/user/<username>')
@login_required
def user(username):
	'''
	User Profile: Displays basic information for given user
	Displays posts given user is tagged in (TODO: include posts their teams are tagged in)
	If you are viewing your own user page, will not be able to submit new tag

	Returns:
		- user.html
	'''
	new_post_form = EditPost()
	user = User.query.filter_by(username=username).first()
	manager = User.query.filter_by(id=user.manager_id).first()
	name = user.firstname

	if user == None:
		flash('User ' + username + ' not found.')
		return redirect(url_for('index'))

	# get all tags that user is tagged in
	tags = Tag.query.filter(and_(Tag.user_tag_id==user.id, Tag.is_deleted==False)).order_by(Tag.time.desc()).all()

	tagged_posts = []
	for tag in tags:
		# for each tag, find post associated with it
		tagged_posts.append(tag.post)

	indented_posts = []
	if len(tagged_posts) != 0:
		indented_posts = posts_to_indented_posts(tagged_posts)

	teams = db.session.query(UserTeam).filter_by(user_id=user.id).all()
	list_of_team_names = []
	for team in teams:
		list_of_team_names.append(team.team.teamname)

	prefill_data = {
		'id': 'u' + str(user.id), # prepend 'u' to differentiate from team id's
		'name': user.firstname + ' ' + user.lastname,
	}

	return render_template('user.html',
		new_post_form=new_post_form,
		user=user,
		posts=indented_posts,
		list_of_team_names=list_of_team_names,
		manager=manager,
		name=name,
		prefill_data=prefill_data,
	)


@app.route('/sign_s3_upload/')
@login_required
def sign_s3_upload():
	'''
	Uploads image files chosen with Dropbox Chooser to S3 account when submitting new post
	Called from s3_upload in kudos.js
	TODO: Think through other abuse scenarios (ex. delete any uploads that aren't referenced with a user)

	Returns:
		- json including the signed request and public url for the thumbnail image
	'''

	AWS_ACCESS_KEY = settings.image_store.aws_credentials.access_key_id
	AWS_SECRET_KEY = settings.image_store.aws_credentials.secret_access_key
	S3_BUCKET = settings.image_store.bucket_name

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



@app.route('/send_error_msg', methods=['POST'])
def send_error_msg():
	'''
	Sends an email to send in case of error in ajax request
	Currently, only information sent from server is the logged in user

	Args (from ajax request):
		- text: error message passed from error handler

	Returns:
		- 'complete'
	'''

	form = request.form
	sender = g.user.email
	reply_to = sender
	recipient_list = ["mskeving@gmail.com"]
	subject = "Kudos Error from %s!" %(g.user.username)
	text = form.get('error_msg')

	kudos_header = "Error from %s" %(g.user.username)
	html = render_template('feedback_email.html',
		text=text,
		kudos_header=kudos_header,
	)
	# need to include post_id param when called send_email, but error won't necessarily have one
	post_id = None

	if settings.email_stealer is None:
		# only send error emails on prod
		send_email(sender, recipient_list, reply_to, subject, html, post_id)

	return "complete"



@app.route('/createpost', methods=['POST'])
@login_required
def new_post():
	'''
	Submit the new post to db with all user/team tags associated with it

	Args (from ajax request):
		- photo_url: url of image form dropbox chooser. If nothing selected, null
		- post_text: text submitted by user
		- tag_ids: team or user id's of tags chosen (| delimited string)
		- tag_text: username or teamname of tags chosen (| delimited string)

	Returns:
		-json including post.html as post_page, post_id of new post, tagged user and team id's
	'''
	user_id = g.user.id
	new_post_form = EditPost()

	form = request.form
	photo_url = form.get('photo_url')
	post_text = form.get('post_text')

	new_post = Post(body=post_text, time=datetime.utcnow(), user_id=user_id, photo_link=photo_url)
	db.session.add(new_post)
	db.session.commit()
	db.session.refresh(new_post)
	post_id = new_post.id

	# create lists of tag information from hidden fields
	tag_ids = form.get('hidden_tag_ids', '').split('|')
	tag_text = form.get('hidden_tag_text', '').split('|')
	seen_already = set()
	tagged_user_ids = []
	tagged_team_ids = []
	for i in range(len(tag_ids)-1): #last index will be "" because of delimiters
		if tag_ids[i] in seen_already:
			# prevent duplicates of tags on single post in case of error submitting post the first time
			continue
		seen_already.add(tag_ids[i])

		#USER TAGS
		if tag_ids[i][0] == 'u':
			user_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
			new_tag = Tag(user_tag_id=user_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())
			tagged_user_ids.append(user_id)
			db.session.add(new_tag)

		#TEAM TAGS
		elif tag_ids[i][0] == 't':
			team_id = int(tag_ids[i][1:]) #remove leading 't' to convert back to int team_id
			new_tag = Tag(team_tag_id=team_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())
			tagged_team_ids.append(team_id)
			db.session.add(new_tag)
	db.session.commit()

	db.session.refresh(new_post)
	posts=[new_post,]
	indented_post = posts_to_indented_posts(posts)[0]

	post_page = render_template('post.html',
		post=indented_post,
		new_post_form=new_post_form,
	)


	post_info_dict = {
		'new_post': post_page,
		'post_id': post_id,
		'tagged_user_ids': tagged_user_ids,
		'tagged_team_ids': tagged_team_ids
	}

	return json.dumps(post_info_dict)


@app.route('/display_single_post', methods=['POST'])
@login_required
def display_single_post():
	'''
	View single post page from email link or by clicking on date of post

	Args:
		post_id: post id of post to display

	Returns:
		post.html
	'''
	new_post_form = EditPost()
	form = request.form
	post_id = form.get('post_id')

	post = Post.query.filter(and_(Post.id==post_id, Post.is_deleted==False)).one()
	indented_post = posts_to_indented_posts([post,])[0]

	return render_template('post.html',
		post=indented_post,
		new_post_form=new_post_form,
	)


@app.route('/create_notifications', methods=["POST"])
def create_notifications():
	'''
	Email notifications created when a user is tagged in a post

	Args:
		- parent_post_id: post id of post with activity
		- tagged_team_ids: ids of any teams tagged in post
		- tagged_user_ids: ids of any users tagged in post
		- post_text: body of post
		- photo_url: url for post image, if included
		- is_new_post: only available if user is submitting a new post
		- is_comment: only available if user is submitting a comment

	Returns:
		- 'complete'
	'''

	form = request.form
	parent_post_id = form.get('parent_post_id')
	tagged_user_ids = json.loads(form.get('tagged_user_ids'))
	tagged_team_ids = json.loads(form.get('tagged_team_ids'))
	photo_url = form.get('photo_url')
	post_text = form.get('post_text')

	is_comment = form.get('is_comment')
	if is_comment:
		if tagged_user_ids:
			subject = "New comment on your Kudos"
			header = g.user.firstname + " " + g.user.lastname + " commented on a Kudos you're tagged in"
			tagged_users = User.query.filter(User.id.in_(tagged_user_ids)).all()
			create_notification_for_tagged_users(tagged_users, photo_url, post_text, parent_post_id, subject, header)
		if tagged_team_ids:
			subject = "New comment on your Kudos"
			header = g.user.firstname + " " + g.user.lastname + " commented on a Kudos your team is tagged in"
			users_teams_in_tagged_teams = UserTeam.query.filter(UserTeam.team_id.in_(tagged_team_ids)).all()
			create_notification_for_tagged_teams(users_teams_in_tagged_teams, photo_url, post_text, parent_post_id, subject, header)
		return "complete"

	is_new_post = form.get('is_new_post')
	if is_new_post:
		if tagged_user_ids:
			subject = "Kudos to you!"
			header = g.user.firstname + " " + g.user.lastname + " sent you a Kudos"
			tagged_users = User.query.filter(User.id.in_(tagged_user_ids)).all()
			create_notification_for_tagged_users(tagged_users, photo_url, post_text, parent_post_id, subject, header)
			create_notification_for_managers(tagged_users, photo_url, post_text, parent_post_id)

		if tagged_team_ids:
			subject = "Kudos to your team!"
			header = g.user.firstname + " " + g.user.lastname + " sent your team a Kudos"
			users_teams_in_tagged_teams = UserTeam.query.filter(UserTeam.team_id.in_(tagged_team_ids)).all()
			create_notification_for_tagged_teams(users_teams_in_tagged_teams, photo_url, post_text, parent_post_id, subject, header)

	return "complete"

def create_notification_for_tagged_users(tagged_users_list, photo_url, post_text, parent_post_id, subject, header):
	'''
	Sets up recipient list for any users tagged in post
	Calls generate_email to render email template
	'''
	recipient_list=[]
	for user_object in tagged_users_list:
		if user_object != g.user:
			recipient_list.append(user_object.email)

	#create notification for taggees
	generate_email(header, post_text, subject, recipient_list, parent_post_id, photo_url)

def create_notification_for_tagged_teams(users_teams_in_tagged_teams, photo_url, post_text, post_id, subject, header):
	# TODO: separate notifications for different teams. {teamname:[list_of_team_members],}
	recipient_list = []
	for user_team in users_teams_in_tagged_teams:
		if user_team.user_id != g.user.id:
			recipient_list.append(user_team.user.email)
	generate_email(header, post_text, subject, recipient_list, post_id, photo_url)


def create_notification_for_managers(tagged_users_list, photo_url, post_text, post_id):
	'''
	Sets up recipient list for any managers of users tagged in post
	If multiple users are tagged in post with same manager, manager receives one email with list of reports
	Managers will only receive notifications when their reports are first tagged in a post. Nothing for comments
	Calls generate_email to render email template

	Args:
		tagged_users_list: list of users tagged
		photo_url: url for photo associated with post
		post_text: body of post
		post_id: post id

	Returns:
		None
	'''

	manager_to_reports_dict = defaultdict(list)
	for user_object in tagged_users_list:
		manager_to_reports_dict[user_object.manager_id].append(user_object)

	manager_ids_list = manager_to_reports_dict.keys()

	manager_objects_to_notify = []
	if len(manager_ids_list) > 0:
		manager_objects_to_notify = User.query.filter(User.id.in_(manager_ids_list)).all()

	for manager in manager_objects_to_notify:
		reports_objects = manager_to_reports_dict.get(manager.id)
		if g.user == manager:
			# don't send email to manager if they are person creating the post
			continue

		recipient_list = [manager.email]
		subject = "Kudos to your team members!"
		if len(reports_objects) == 1:
			subject = "Kudos to your team member, " + str(reports_objects[0].firstname) + "!"
			header = "As " + str(reports_objects[0].firstname) + "'s lead, we want you to know that " + g.user.firstname + " " + g.user.lastname + " sent them this Kudos:"
		elif len(reports_objects) == 2:
			subject = "Kudos to your team members, " + str(reports_objects[0].firstname) + " and " + str(reports_objects[1].firstname) + "!"
			header = "As their team lead, we want you to know that " + g.user.firstname + " " + g.user.lastname + " sent them this Kudos:"
		elif len(reports_objects) > 2:
			reports_str = ""
			for report in reports_objects[:-1]:
				reports_str += str(report.firstname) + ", "
			header = "As " + reports_str + " and " + str(reports_objects[-1].firstname) + "'s lead, we want you to know that " + g.user.firstname + " " + g.user.lastname + " sent them this Kudos:"

		generate_email(header, post_text, subject, recipient_list, post_id, photo_url)


def generate_email(header, message, subject, recipient_list, post_id, img_url):
	'''
	renders notification_email.html with parameters
	Calls send_email to actually send

	Args:
		- header: String to go at top of email body
		- message: post body to be displayed in email
		- subject: email subject
		- recipient_list: list of email recipients
		- post_id: post id
		- img_url: url for photo

	Returns:
		None
	'''

	reply_to = g.user.email

	html = render_template('notification_email.html',
		kudos_header=header,
		message=message,
		img_url=img_url,
		post_id=post_id,
		)
	sender = settings.mail_sender.username
	send_email(sender, recipient_list, reply_to, subject, html, post_id)


def send_email(sender, recipients, reply_to, subject, html, post_id):
	'''
	Sends emails to list of recipients
	if there is an email_stealer from settings.py, send all emails to this address (for testing) with custom subject
	emails are sent asynchronously with send_async

	Args:
		- sender: email address notifications will be coming from
		- recipients: list of email recipients
		- reply_to: reply_to email address
		- subject: email subject
		- html: rendered template for notificaiton_email.html
		-post_id: post id

	Returns:
		None
	'''

	if settings.email_stealer is not None:
		subject = "%s (%s)" % (subject, ', '.join(recipients))
		recipients = [settings.email_stealer]

	msg = Message(
		subject=subject,
		sender=sender,
		recipients=recipients,
		reply_to=reply_to,
		html=html,
	)

	def send_async(my_app, msg):
		with my_app.app_context():
			mail.send(msg)
			print "email sent to %r, post_id: %r" % (msg.recipients, post_id)

	Thread(target=send_async, args=[app,msg]).start()


@app.route('/removethanks', methods=['POST'])
@login_required
def remove_thanks():
	'''
	Users can remove thanks they've given (is_deleted=True)

	Args (from ajax request):
		post_id: post id of their thank

	Returns:
		- 'complete'
	'''

	form = request.form

	thanks_sender = g.user.id
	post_id = form.get('post_id')

	delete_thanks = Thanks.query.filter(and_(Thanks.thanks_sender==thanks_sender, Thanks.post_id==post_id)).all()

	for thank in delete_thanks:
		thank.is_deleted = True
	db.session.commit()

	return "complete"

# currently not used anywhere.
@app.route('/displaythanks', methods=['POST'])
@login_required
def display_thanks():

	thanks = Thanks.query.filter(Thanks.post_id==post_id).all()
	thankers = []
	for thank in thanks:
		thankers.append(thank.thanker)

	return thankers


@app.route('/newtag', methods=['POST'])
@login_required
def add_tag():
	'''
	Add new user or team tag to post
	Id's for users and teams are kept separate and unique by prepending with 'u' or 't'
	TODO: sort of backwards to send this to client and then back to server to send email notifications. Call directly from here

	Args:
		- post_id: post id for parent post
		- tag_ids: | delimited string with user or team ids for tags
		- tag_text: | delimited string with text of tags (team and user names)

	Returns:
		-json including tagged_user_ids and tagged_team_ids
	'''

	user_id = g.user.id
	form = request.form
	post_id = form.get("parent_post_id")

	tag_ids = request.form['tag_ids'].split('|')
	tag_text = request.form['tag_text'].split('|')

	tagged_user_ids = [] # used in kudos.js for send_notifications
	tagged_team_ids = []

	for i in range(len(tag_ids)-1): #last index will be "" because of delimiters
		#USER TAGS
		if tag_ids[i][0] == 'u':
			tag_user_id = int(tag_ids[i][1:]) #remove leading 'u' to convert back to int user_id
			new_tag = Tag(user_tag_id=tag_user_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())

			tagged_user = User.query.filter_by(id=tag_user_id).first()
			# get tag information to create avatars client side
			db.session.add(new_tag)

			tagged_user_ids.append(tagged_user.id)

		#TEAM TAGS
		if tag_ids[i][0] == 't':
			tag_team_id = int(tag_ids[i][1:]) #remove leading 't' to convert back to int team_id
			new_tag = Tag(team_tag_id=tag_team_id, body=tag_text[i], post_id=post_id, tag_author=user_id, time=datetime.utcnow())

			tagged_team = Team.query.filter_by(id=tag_team_id).first()
			db.session.add(new_tag)

			tagged_team_ids.append(tagged_team.id)

	db.session.commit()

	new_tag_dict={}
	new_tag_dict['tagged_user_ids'] = tagged_user_ids
	new_tag_dict['tagged_team_ids'] = tagged_team_ids
	tag_info_json = json.dumps(new_tag_dict)

	return tag_info_json


#DELETE TAGS
@app.route('/deletetag', methods=['GET','POST'])
@login_required
def delete_tag():
	'''
	Remove tags from an existing post

	Args:
		- tag_id: tag id (not user or team id)

	Returns:
		- json including user_ids and team_ids
	'''

	form = request.form
	tag_id = form.get('tag_id')

	delete_tag = db.session.query(Tag).filter_by(id=tag_id).one()
	if delete_tag.user_tag_id:
		tag_info = {'user_id': delete_tag.user_tag_id}
	elif delete_tag.team_tag_id:
		tag_info = {'team_id': delete_tag.team_tag_id}

	delete_tag.is_deleted = True
	db.session.commit()

	return json.dumps(tag_info)


@app.route('/newcomment', methods=['POST'])
@login_required
def new_comment():
	'''
	Called whenever you click 'Thank', whether you include a comment or not.
	If user does not include text, body is stored as an empty string.

	Tags for the parent post are queried so email notifications can be sent with new comment.
	Notifications are only sent to taggees if text is included

	Args:
		- body: post body
		- parent_post_id: post id
		- tag_ids: | delimited string with user or team ids for tags
		- tag_text: | delimited string with text of tags (team and user names)

	Returns:
		-json including comment.html, tagged_user_ids, and tagged_team_ids
	'''

	form = request.form

	body = form.get('post_text')
	parent_post_id = form.get('parent_post_id')

	parent_post = Post.query.filter(and_(Post.id==parent_post_id, Post.is_deleted==False)).first()
	if not parent_post:
		comment_info = {"is_error": True}
		return json.dumps(comment_info)

	new_comment = Post(body=body, parent_post_id=parent_post_id, time=datetime.utcnow(), user_id=g.user.id)
	db.session.add(new_comment)
	db.session.commit()

	tag_ids = form.get('hidden_tag_ids', '').split('|')
	tag_text = form.get('hidden_tag_text', '').split('|')

	tags_for_parent_post = Tag.query.filter(and_(Tag.post_id==parent_post_id, Tag.is_deleted==False)).all()

	#get tag information to send notifications
	tagged_user_ids = []
	tagged_team_ids = []
	for tag in tags_for_parent_post:
		if tag.user_tag_id:
			tagged_user_ids.append(tag.user_tag_id)
		if tag.team_tag_id:
			tagged_team_ids.append(tag.team_tag_id)

	comment_template = render_template("comment.html",
			comment=new_comment)

	comment_info = {
		'comment_template': comment_template,
		'tagged_user_ids': tagged_user_ids,
		'tagged_team_ids': tagged_team_ids
	}

	return json.dumps(comment_info)



@app.route('/deletepost', methods=['POST', 'GET'])
@login_required
def delete_post():
	'''
	Called to remove a parent post or any thanks/comments
	To delete post, must also delete associated tags, comments, and thanks

	Args:
		- post_id: post id of parent_post or comment to remove

	Returns:
		- post_id
	'''

	form = request.form
	post_id = form.get('post_id')

	delete_post = db.session.query(Post).filter_by(id=post_id).first()
	if delete_post:
		delete_post.is_deleted = True

		#delete post, replies, associatated tags, and thanks
		to_delete_list = []
		to_delete_list.append(delete_post)
		for tag in delete_post.tags:
			tag.is_deleted = True
		for comment in delete_post.children:
			comment.is_deleted = True
		for thank in delete_post.thanks:
			thank.is_deleted = True

		db.session.commit()

	return post_id



@app.route('/tagged_in_post', methods=['POST'])
def tagged_in_post():
	'''
	called from kudos.js to display text for all tags in a post
	Used if tags needs to be truncated.

	Args:
		post_id: post id

	Returns:
		tagged_modal.html, which displays simple list of names in lightbox
	'''
	form = request.form
	post_id = form.get('post_id')

	post = Post.query.filter(and_(Post.id==post_id, Post.is_deleted==False)).all()

	indented_post = posts_to_indented_posts(post)[0]
	tagged_users_tag_objects = indented_post['tagged_users']
	tagged_teams_tag_objects = indented_post['tagged_teams']

	if post:
		return render_template('tagged_modal.html',
			tagged_teams=tagged_teams_tag_objects,
			tagged_users=tagged_users_tag_objects)
	return render_template('tagged_modal.html',
			error_msg="No Post Found")



@app.route('/post/<post_id>', methods=['GET'])
@login_required
def permalink_for_post_with_id(post_id):
	'''
	Displays a single post
	Link to this in notification emails, or when you click on date for a given post

	Returns:
		postpage.html
	'''
	new_post_form = EditPost()
	posts = Post.query.filter(and_(Post.id==int(post_id), Post.is_deleted==False)).all()
	if posts:
		post = posts_to_indented_posts(posts)[0]
		return render_template('postpage.html',
		user=g.user,
		post=post,
		new_post=new_post,
		new_post_form=new_post_form,
		)

	else:
		return render_template('postpage.html',
			error_msg="Sorry! This post has been removed"
		)


@app.route('/all_users')
@login_required
def all_users():
	'''
	Display all active users and teams they're on
	TODO: Think more about performance here.
		-Infinite scrolling to display more teams? Load a fraction first to get something loaded on page and then display more?

	Returns:
		allusers.html
	'''
	all_users = User.query.filter(User.is_deleted==False).options(joinedload_all(User.users_teams, 'team')).order_by(User.firstname, User.lastname, User.employee_id).all()

	all_user_ids = []
	for user in all_users:
		all_user_ids.append(user.id)

	dict_of_users_teams = {}
	for user in all_users:
		user_teams = sorted(user.users_teams, cmp=lambda x, y: cmp(x.id, y.id))
		dict_of_users_teams[user.id] = [ut.team for ut in user_teams]

	return render_template('allusers.html',
		all_users=all_users,
		user_teams_dict=dict_of_users_teams,
		)



def posts_to_indented_posts(posts):
	'''
	Transforms a list of posts to a list of dictionaries with relevant post information
	TODO: rename to something more relevant. Was originally created to display posts and their children (indented on the page)

	Args:
		- posts: LIST of posts

	Returns:
		- List of dictionaries for each post with relevant information for easy retrieval (ex. taggees, thankers, comments etc)
	'''

	indented_posts = []

	for p in posts:

		d = {}
		d['post_object'] = p
		d['indent'] = 0

		author_teams = []
		user_teams= UserTeam.query.filter(UserTeam.user_id==p.author.id).all()
		for team in user_teams:
			if team.is_deleted == False:
				author_teams.append(team.team)
		d['author_teams'] = author_teams

		children = []
		commenters = []
		for child in p.children:
			if child.is_deleted == False:
				children.append(child)
				commenters.append(child.author)
		d['commenters'] = commenters
		d['comments'] = children

		tagged_users = []
		tagged_teams = []
		for tag in p.tags:
			if tag.user_tag_id:
				if tag.is_deleted == False:
					tagged_users.append(tag)
			elif tag.team_tag_id:
				if tag.is_deleted == False:
					tagged_teams.append(tag)
			else:
				print "no tags for this post.id: %r" % p.id

		# display tags in random order each time
		random.shuffle(tagged_users)
		random.shuffle(tagged_teams)
		d['tagged_users'] = tagged_users
		d['tagged_teams'] = tagged_teams

		all_tags  = tagged_teams + tagged_users
		d['all_tags'] = all_tags

		# list of users giving thanks for post
		thankers = []
		for thank in p.thanks:
			thankers.append(thank.user)
		d['thankers'] = thankers

		d['time'] = p.time.strftime("%m/%d/%Y")

		# admin who approves/rejects post for TV display. Only used on /admin
		d['status_committer'] = p.status_committer

		indented_posts.append(d)

	return indented_posts


# @app.errorhandler(404)
# def internal_error(error):
# 	return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_error(error):
# 	db.session.rollback()
# 	return render_template('500.html'), 500


