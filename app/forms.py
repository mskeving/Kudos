from flask.ext.wtf import Form, HiddenField

class EditPost(Form):
	hidden_tag_ids = HiddenField('hidden_tag_ids')
	hidden_tag_text = HiddenField('hidden_tag_text')
