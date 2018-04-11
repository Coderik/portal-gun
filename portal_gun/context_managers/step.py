from __future__ import print_function
import sys


class step(object):
	_message_width = 40
	_filling_character = ' '

	@staticmethod
	def set_message_width(value):
		step._message_width = value

	@staticmethod
	def set_filling_character(value):
		step._filling_character = value

	def __init__(self, message, error_message=None, catch=None):
		"""
		:param message: Text to be printed for the step.
		:param error_message: Error message to override actually caught exception.
		:param catch: List of exceptions to catch (by default catch everything) and wrap in StepError.
		"""
		self._title = message
		self._errors = catch or [Exception]
		self._error_message = error_message

	def __enter__(self):
		print('{msg:{fill}<{width}}'
			  .format(msg=self._title, fill=step._filling_character, width=step._message_width), end='')

		# Ensure stdout is flushed immediately
		sys.stdout.flush()

		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is None:
			print('OK')
		else:
			print('ERROR')
			for err in self._errors:
				if issubclass(exc_type, err):
					# Suppress expected error
					if self._error_message is not None:
						raise StepError('{}'.format(self._error_message))
					else:
						raise StepError('{}'.format(exc_value))

			# Do not suppress unexpected errors
			return False


class StepError(Exception):
	def __init__(self, message=None):
		super(StepError, self).__init__(message)

	def __srt__(self):
		return self.message

	def __repr__(self):
		return self.message
