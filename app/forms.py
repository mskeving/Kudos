from flask.ext.wtf import Form, TextField, BooleanField, TextAreaField, SubmitField, HiddenField
from flask.ext.wtf import Required, Length
from app.models import User



class LoginForm(Form):
	openid = TextField('openid', validators = [Required()]) #required checks to make sure field isn't empty
	remember_me = BooleanField('remember_me', default = False)



class EditForm(Form):
	nickname = TextField('nickname', validators = [Required()])
	about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])

	def __init__(self, original_nickname, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.original_nickname = original_nickname

	def validate(self):
		#check to see if nickname has been used already
		if not Form.validate(self):
			return False
		if self.nickname.data == self.original_nickname:
			#if new nickname is the same, accept it
			return True
		user = User.query.filter_by(nickname = self.nickname.data).first()
			#otherwise check to see if it exists elsewhere in DB
		if user != None:

			self.nickname.errors.append('This nickname is already in use. Please choose another one.')
			return False
		return True	



class EditPost(Form):
	post_body = TextAreaField('post_body', validators = [Required()])
	post_submit_btn = SubmitField('post_submit_btn')
	post_delete_btn = SubmitField('post_delete_btn')
	post_id = HiddenField("post_id") #validator that this is number

class DeletePost(Form):
	post_id = HiddenField("post_id") #validator that this is number
	post_delete_btn = SubmitField('post_delete_btn')

