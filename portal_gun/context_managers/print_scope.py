from contextlib import contextmanager

from portal_gun.context_managers.print_indent import print_indent


@contextmanager
def print_scope(prologue, epilogue=None, indent=None):
	"""
	Context manager for enclosing any output within a prologue and
	(optionally) an epilogue lines. The output is also implicitly indented.
	"""

	print(prologue)

	with print_indent(indent):
		yield

	if epilogue is not None:
		print(epilogue)


def set_default_indent(value):
	"""
	Conventional setter for the size of the global default indent.
	:param value: Indent size.
	"""

	print_indent.set_default_indent(value)
