class BaseField(object):
	def __init__(self, is_required):
		self._is_required = is_required

	def is_required(self):
		return self._is_required

	def __str__(self):
		return 'required' if self._is_required else 'optional'
