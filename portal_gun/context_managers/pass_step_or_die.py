from __future__ import print_function


class PassStepOrDie(object):
	_message_width = 40
	_filling_character = ' '
	_message_offset = '\t'
	_error_offset = '\t\t'
	_tab_width = 4

	@staticmethod
	def set_message_width(value):
		PassStepOrDie._message_width = value

	@staticmethod
	def set_filling_character(value):
		PassStepOrDie._filling_character = value

	@staticmethod
	def set_message_offset(value):
		PassStepOrDie._message_offset = value

	@staticmethod
	def set_error_offset(value):
		PassStepOrDie._error_offset = value

	def __init__(self, check_message, failure_message, errors=None, print_error=True):
		self._check_message = check_message
		self._errors = errors or [Exception]
		self._failure_message = failure_message
		self._print_error = print_error

	def __enter__(self):
		print('{offset}{msg:{fill}<{width}}'
			  .format(msg=self._check_message,
					  fill=PassStepOrDie._filling_character,
					  width=PassStepOrDie._message_width,
					  offset=PassStepOrDie._message_offset)
			  .expandtabs(PassStepOrDie._tab_width),
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
						exit('{offset}{}: {}'
							 .format(self._failure_message, exc_value, offset=PassStepOrDie._error_offset)
							 .expandtabs(PassStepOrDie._tab_width))
					elif self._failure_message is not None:
						exit('{offset}{}'
							 .format(self._failure_message, offset=PassStepOrDie._error_offset)
							 .expandtabs(PassStepOrDie._tab_width))
					elif self._print_error:
						exit('{offset}{}'
							 .format(exc_value, offset=PassStepOrDie._error_offset)
							 .expandtabs(PassStepOrDie._tab_width))
					else:
						exit()

			# Do not suppress unexpected errors
			return False


def pass_step_or_die(check_message, failure_message, errors=None, print_error=True):
	return PassStepOrDie(check_message, failure_message, errors, print_error)
