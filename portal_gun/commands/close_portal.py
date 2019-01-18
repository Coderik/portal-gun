

from portal_gun.commands.helpers import get_provider_config, get_portal_spec, get_portal_name, \
	get_provider_from_portal
from portal_gun.context_managers.print_scope import print_scope
from .base_command import BaseCommand
from .handlers import create_handler


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
			portal_name = get_portal_name(self._args.portal)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args.config, provider_name)

		# Create appropriate command handler for given cloud provider
		handler = create_handler(provider_name, provider_config)

		handler.close_portal(portal_spec, portal_name)
