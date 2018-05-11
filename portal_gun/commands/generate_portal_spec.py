import json
from os import path

from portal_gun.configuration.helpers import get_portal_name
from .base_command import BaseCommand
from .handlers import generate_portal_spec


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

	def run(self):
		provider_name = 'aws'

		# Get portal name
		portal_name = get_portal_name(self._args)

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
