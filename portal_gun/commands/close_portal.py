from __future__ import print_function

from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.handlers import AwsHandler
from portal_gun.configuration.helpers import get_config, get_portal_spec
from portal_gun.context_managers.print_scope import print_scope


class ClosePortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'close'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Close portal')
		parser.add_argument('portal', help='Name of portal')

	def run(self):
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create appropriate command handler
		handler = AwsHandler(config)

		handler.close_portal(portal_spec, portal_name)
