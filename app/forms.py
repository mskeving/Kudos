from flask.ext.wtf import Form, TextField, BooleanField, TextAreaField, SubmitField, HiddenField
from flask.ext.wtf import Required, Length
from app.models import User

class EditPost(Form):
	hidden_tag_ids = HiddenField('hidden_tag_ids')
	hidden_tag_text = HiddenField('hidden_tag_text')
