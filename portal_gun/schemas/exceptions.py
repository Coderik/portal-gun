class ConfigValidationError(Exception):
	def __init__(self, message):
		self.message = message


class MissingFieldError(ConfigValidationError):
	def __init__(self, trace):
		message = 'Required field `{}` is missing'.format('.'.join(trace))
		ConfigValidationError.__init__(self, message)


class WrongFieldTypeError(ConfigValidationError):
	def __init__(self, trace, expected_type):
		message = 'Field `{}` is expected to have type {}'.format('.'.join(trace), expected_type)
		ConfigValidationError.__init__(self, message)
