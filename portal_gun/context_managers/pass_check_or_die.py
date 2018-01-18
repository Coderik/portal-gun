class PassCheckOrDie(object):
	_message_width = 40
	_filling_character = ' '

	@staticmethod
	def set_message_width(value):
		PassCheckOrDie._message_width = value

	@staticmethod
	def set_filling_character(value):
		PassCheckOrDie._filling_character = value

	def __init__(self, check_message, failure_message, errors=None, print_error=True):
		self._check_message = check_message
		self._errors = errors or [Exception]
		self._failure_message = failure_message
		self._print_error = print_error

	def __enter__(self):
		print('\t{msg:{fill}<{width}}'.format(msg=self._check_message,
											  fill=PassCheckOrDie._filling_character,
											  width=PassCheckOrDie._message_width),
			  end='')
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is None:
			print('OK')
		else:
			print('ERROR')
			for err in self._errors:
				if issubclass(exc_type, err):
					# Print expected error and exit
					if self._failure_message is not None and self._print_error:
						exit('\t\t{}: {}'.format(self._failure_message, exc_value))
					elif self._print_error:
						exit('\t\t{}'.format(exc_value))
					else:
						exit()

			# Do not suppress unexpected errors
			return False


def pass_check_or_die(check_message, failure_message, errors=None, print_error=True):
	return PassCheckOrDie(check_message, failure_message, errors, print_error)
