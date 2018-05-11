from portal_gun.configuration.helpers import get_provider_config, get_portal_spec, get_portal_name, \
	get_provider_from_portal
from portal_gun.context_managers.no_print import no_print
from portal_gun.context_managers.print_scope import print_scope
from .base_command import BaseCommand
from .handlers import create_handler


class ShowPortalInfoCommand(BaseCommand):
	FIELDS = ['name', 'status', 'id', 'type', 'user', 'host', 'ip', 'remote', 'key']

	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'info'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Show information about portal')
		parser.add_argument('portal', help='Name of portal')
		parser.add_argument('-f', '--field', dest='field', help='Print value for a specified field ({}).'
							.format(', '.join(cls.FIELDS)))

	def run(self):
		if self._args.field is not None:
			# Get value of the specified field and print it
			value = self.get_field(self._args.field)
			if value is not None:
				print value
		else:
			self.show_full_info()

	def get_field(self, field):
		# Ensure field name is valid
		if field not in self.FIELDS:
			return None

		with no_print():
			# Find, parse and validate configs
			portal_name = get_portal_name(self._args)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args, provider_name)

			# Create appropriate command handler for given cloud provider
			handler = create_handler(provider_name, provider_config)

			return handler.get_portal_info_field(portal_spec, portal_name, field)

	def show_full_info(self):
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			portal_name = get_portal_name(self._args)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args, provider_name)

		# Create appropriate command handler for given cloud provider
		handler = create_handler(provider_name, provider_config)

		handler.show_portal_info(portal_spec, portal_name)
