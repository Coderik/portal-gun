from __future__ import print_function

from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.handlers import AwsHandler
from portal_gun.configuration.helpers import get_config, get_portal_spec
from portal_gun.context_managers.print_scope import print_scope


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'open'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Open portal')
		parser.add_argument('portal', help='Name of portal')

	# TODO: add verbose mode that prints all configs and dry-run mode to check the configs and permissions
	def run(self):
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create appropriate command handler
		handler = AwsHandler(config)

		handler.open_portal(portal_spec, portal_name)
