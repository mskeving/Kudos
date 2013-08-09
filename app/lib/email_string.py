from flask import render_template

def gen_email_string(href, **kw):
	""" @param href - the url that the button in the email should take the user to
		@param message - the message from the kudos-giver to the kudos-receiver """
	default_subs = {
		'href': href,
		'message': '',
		'sender_name': 'Someone'
	}

	for key, value in kw.iteritems():
		default_subs[key] = value
	return render_template('email.html', **default_subs)

if __name__ == '__main__':
	""" print out the result of gen_email_string for some example input"""
	print gen_email_string(
		'www.google.com',
		message="Here's a message from the person who sent you Kudos! They think you're swell.",
        sender_name="bob",
		)

