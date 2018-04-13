from os import path

from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.schemas import PortalSchema


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
		print('Creating draft specification for `{}` portal.'.format(portal_name))

		# Ensure file with this name does not exist
		file_name = '{}.json'.format(portal_name)
		if path.exists(file_name):
			print('File `{}` already exists. Remove the file or pick different name for the portal.'.format(file_name))
			return

		# Generate spec and pretty print it to JSON
		spec_str = PortalSchema().dumps(None, indent=4)

		# Write spec to file
		with open(file_name, 'w') as f:
			f.write(spec_str)

		print('Draft of portal specification has been written to `{}`.'.format(file_name))
