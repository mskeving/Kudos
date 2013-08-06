from app import db
from datetime import datetime
from hashlib import md5

ROLE_USER = 0
ROLE_ADMIN = 1

class Team(db.Model):
	__tablename__ = "teams"

	id = db.Column(db.Integer, primary_key = True)
	teamname = db.Column(db.String(120), index = True)

	teams = db.relationship('UserTeam', backref = 'team')

class UserTeam(db.Model):
	__tablename__ = "users_teams"

	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

	__table_args__ = (
		db.UniqueConstraint('user_id', 'team_id'),
		)

class User(db.Model):
	__tablename__ = "users"

	id = db.Column(db.Integer, primary_key = True)
	photo = db.Column(db.String(120))
	firstname = db.Column(db.String(64), index = True)
	lastname = db.Column(db.String(64), index = True)
	#change nickname unique=false
	nickname = db.Column(db.String(64), index = True, unique = True)
	email = db.Column(db.String(120), index = True, unique = True)
	phone = db.Column(db.String(25), index = True)
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.Date)

	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
	users = db.relationship('UserTeam', backref = 'user')

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

	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.String(140))
	parent_post_id = db.Column(db.Integer) #denotes that it's a reply
	timestamp = db.Column(db.Date)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id')) #users is tablename
	tags = db.Column(db.Text)
	#tags - store as JSON db.Text


	#Post.author (because of backref in User)


	def __repr__(self):
		return '<Post %r>' %(self.body)






