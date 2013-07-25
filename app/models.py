from app import db
from datetime import datetime
from hashlib import md5

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key = True)
	firstname = db.Column(db.String(64), index = True)
	lastname = db.Column(db.String(64), index = True)
	#change nickname unique=false
	nickname = db.Column(db.String(64), index = True, unique = True)
	email = db.Column(db.String(120), index = True, unique = True)
	phone = db.Column(db.String(25), index = True)
	team = db.Column(db.String(120), index = True)
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.Date)
	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
	#backref is adding author to Post class
	#lazy.. whether all posts are loaded at the same time as user. look up options


	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname = nickname).first() == None:
			return nickname
			version = 2
			while True:
				new_nickname = nickname + str(version)
				if User.query.filter_by(nickname = new_nickname).first() == None:
					break
				version += 1
			return new_nickname

	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)
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

	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.Date)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id')) #users is tablename
	#Post.author (because of backref in User)
	#relationship with user table?

	def __repr__(self):
		return '<Post %r>' %(self.body)