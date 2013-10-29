from app import app, db

import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key

class Team(db.Model):
	__tablename__ = "teams"

	id = db.Column(db.Integer, primary_key=True)
	teamname = db.Column(db.String(120), index=True)
	photo = db.Column(db.String(120))
	tagged_in = db.relationship('Tag', backref='team_tag')
	teams = db.relationship('UserTeam', backref='team')
	# ex) query results from UserTeam: 
	# for team in userteams:
	# 	team.team.teamname

class UserTeam(db.Model):
	__tablename__ = "users_teams"

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

	__table_args__ = (
		db.UniqueConstraint('user_id', 'team_id'),
		)

class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key=True)
	employee_id = db.Column(db.Integer)
	firstname = db.Column(db.String(64), index=True)
	lastname = db.Column(db.String(64), index=True)
	#change nickname unique=false
	nickname = db.Column(db.String(64), index=True)
	email = db.Column(db.String(120), index=True, unique=True)
	photo = db.Column(db.String(120))
	phone = db.Column(db.String(25), index=True)
	username = db.Column(db.String(68))
	manager_id = db.Column(db.Integer, nullable=True)

	posts = db.relationship('Post', backref='author', lazy='dynamic')
	users = db.relationship('UserTeam', backref='user', primaryjoin="User.id==UserTeam.user_id")
	tagged_in = db.relationship('Tag', backref='user_tag', primaryjoin="User.id==Tag.user_tag_id", lazy="dynamic'")
	thanker = db.relationship('Thanks', backref='user')


	#backref is adding author to Post class
	#lazy.. whether all posts are loaded at the same time as user. look up options



	def generate_photo_url(self, expires_in=300):
		#url should be everything after bucket name (dropboxkudos)
		if app.config['USE_S3']:
			if self.photo:
				s3_path = "/avatars_hb/" + os.path.basename(self.photo)
			else:
				s3_path = "/avatars_hb/generic_photo.jpg"
			key = app.config['S3_BUCKET'].new_key(s3_path)
			return key.generate_url(expires_in=expires_in)
		else:
			if self.photo:
				return "/static/img/" + os.path.basename(self.photo)
			return "/static/img/generic_photo.jpg"


	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname=nickname).first() == None:
			return nickname
			version = 2
			while True:
				new_nickname = nickname + str(version)
				if User.query.filter_by(nickname=new_nickname).first() == None:
					break
				version += 1
			return new_nickname

	def avatar(self, size):
		return "Avatar"
		#return "<img src={{ url_for('static', filename='missy.jpg') }} height='%d' width='%d'>" %(size, size)
		#return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)
			#d=mm determines what placehold image is return when user does not have gravatar account (mystery man)

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.id)

	def __repr__(self):
		#tells how to print objects of this class. Used for debugging. 
		return '<User %r>' %(self.nickname)

class Post(db.Model):
	__tablename__ = "posts"

	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	parent_post_id = db.Column(db.Integer, db.ForeignKey('posts.id')) #denotes that it's a reply
	time = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id')) #users is tablename
	photo_link = db.Column(db.String(140))
	tags = db.relationship('Tag', backref='post')
	thanks = db.relationship('Thanks', backref='post')
	children = db.relationship('Post') #when query for posts, post.children will be available


	#rename user_id to author_id to match backref
	#Post.author (because of backref in User)

	def __repr__(self):
		return '<Post %r>' %(self.body)

class Thanks(db.Model):
	__tablename__ = "thanks"

	id = db.Column(db.Integer, primary_key=True)
	thanks_sender = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	time = db.Column(db.DateTime)


class Tag(db.Model):
	__tablename__ = "tags"

	id = db.Column(db.Integer, primary_key=True)
	team_tag_id = db.Column(db.Integer, db.ForeignKey('teams.id'), index=True)
	user_tag_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
	body = db.Column(db.String(200)) #just for readability in DB store string of tag
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	tag_author = db.Column(db.Integer, db.ForeignKey('users.id')) 
	time = db.Column(db.DateTime)



	






