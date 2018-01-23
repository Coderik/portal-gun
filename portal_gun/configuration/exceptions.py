class ConfigValidationError(Exception):
	def __init__(self, message):
		super(ConfigValidationError, self).__init__()
		self.message = message

	def __str__(self):
		return repr(self.message)

	__repr__ = __str__


class MissingFieldError(ConfigValidationError):
	def __init__(self, trace):
		message = 'Required field `{}` is missing'.format('.'.join(trace))
		super(MissingFieldError, self).__init__(message)


class WrongFieldTypeError(ConfigValidationError):
	def __init__(self, trace, actual_type, expected_type):
		message = 'Field `{}` has type `{}` while type `{}` is expected' \
			.format('.'.join(trace), actual_type.__name__, expected_type.__name__)
		super(WrongFieldTypeError, self).__init__(message)


class SchemaError(Exception):
	def __init__(self, message):
		super(SchemaError, self).__init__()
		self.message = message

	def __str__(self):
		return repr(self.message)

	__repr__ = __str__
