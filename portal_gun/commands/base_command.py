class BaseCommand(object):
	""" Base class for all specific Commands. """
	def __init__(self, args):
		self._args = args

	def run(self):
		raise NotImplementedError('Every subclass of BaseCommand should implement run() method.')

	@staticmethod
	def cmd():
		raise NotImplementedError('Every subclass of BaseCommand should implement static cmd() method.')

	@classmethod
	def add_subparser(cls, subparsers):
		raise NotImplementedError('Every subclass of BaseCommand should implement static cmd() method.')

	@staticmethod
	def fill_subparsers(subparsers):
		""" Add subparser for every instance of Command. """

		for cls in BaseCommand.__subclasses__():
			cls.add_subparser(subparsers)

	@staticmethod
	def create_command(cmd, args):
		""" Factory method that creates instances of Commands. """

		for cls in BaseCommand.__subclasses__():
			if cls.cmd() == cmd:
				return cls(args)

		return None

