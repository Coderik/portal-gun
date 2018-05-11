import json
from os import path

from portal_gun.commands.helpers import get_portal_name, get_provider_from_env, get_provider_from_user
from .base_command import BaseCommand
from .handlers import list_providers, describe_providers, generate_portal_spec


class GeneratePortalSpecCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'init'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Generate template specification file for new portal')
		parser.add_argument('portal', help='Name of portal')
		provider_group = parser.add_mutually_exclusive_group()
		for desc in describe_providers():
			provider_group.add_argument('--{}'.format(desc['name']), action='store_const', const=desc['name'],
										dest='provider', help='Set {} as cloud provider'.format(desc['long_name']))

	def run(self):
		providers = list_providers()
		provider_name = self._args.provider or \
						get_provider_from_env(choices=providers) or \
						get_provider_from_user(choices=providers)

		portal_name = get_portal_name(self._args.portal)

		# Confirm portal name to user
		print('Creating draft specification for `{}` portal.'.format(portal_name))

		# Ensure file with this name does not exist
		file_name = '{}.json'.format(portal_name)
		if path.exists(file_name):
			print('File `{}` already exists. Remove the file or pick different name for the portal.'.format(file_name))
			return

		# Generate draft of a portal spec and pretty print it to JSON
		spec_str = json.dumps(generate_portal_spec(provider_name), indent=4)

		# Write portal spec to file
		with open(file_name, 'w') as f:
			f.write(spec_str)

		print('Draft of portal specification has been written to `{}`.'.format(file_name))
