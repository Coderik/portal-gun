class ProviderRequestError(Exception):
	def __init__(self, message):
		super(ProviderRequestError, self).__init__(message)

	def __srt__(self):
		return self.message

	def __repr__(self):
		return self.message
