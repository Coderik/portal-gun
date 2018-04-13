import json
from os import path

from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.generation import generate_portal_spec


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
		# Get portal name
		portal_name = self._args.portal.rsplit('.', 1)[0]

		# Confirm portal name to user
		print('\tWill create draft specification for `{}` portal.'.format(portal_name))

		# Ensure file with this name does not exist
		file_name = '{}.json'.format(portal_name)
		if path.exists(file_name):
			print('\tFile `{}` already exists. Remove the file or pick different name for the portal.'.format(file_name))
			return

		# Generate spec and pretty print it to JSON
		spec = generate_portal_spec()
		spec_str = json.dumps(spec, indent=4, sort_keys=True)

		# Write spec to file
		with open(file_name, 'w') as f:
			f.write(spec_str)

		print('\tDraft of portal specification has been written to `{}`.'.format(file_name))
