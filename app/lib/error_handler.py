import logging
from logging.handlers import SMTPHandler
from settings import settings

class KudosErrorHandler(SMTPHandler):
	def __init__(self):
		m = settings.mail_sender
		credentials = (m.username, m.password) if m.username or m.password else None
		secure = () if m.use_tls else None
		super(KudosErrorHandler, self).__init__(
			mailhost=(m.server, m.port),
			fromaddr=m.reply_to,
			toaddrs=settings.admin_emails,
			subject='Kudos Error',
			credentials=credentials,
			secure=secure
		)
		self.setLevel(logging.ERROR)

	def getSubject(self, record):
		if record.exc_info:
			return record.exc_info[1]
		else:
			return "Kudos Error"