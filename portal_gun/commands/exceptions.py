class CommandError(Exception):
	def __init__(self, message):
		super(CommandError, self).__init__(message)

	def __srt__(self):
		return self.message

	def __repr__(self):
		return self.message
