from flask.ext.wtf import Form, TextField, BooleanField, TextAreaField, SubmitField, HiddenField
from flask.ext.wtf import Required, Length
from app.models import User

class NewReply(Form):
	reply_body = TextAreaField('reply_body', validators = [Required()])
	reply_submit_btn = SubmitField('reply_submit_btn')
	hidden_post_id = HiddenField('post_id') #validator that this is number

class EditPost(Form):
	hidden_tag_ids = HiddenField('hidden_tag_ids')
	hidden_tag_text = HiddenField('hidden_tag_text')

class DeletePost(Form):
	hidden_post_id = HiddenField('post_id') #validator that this is number
	post_delete_btn = SubmitField('post_delete_btn')


