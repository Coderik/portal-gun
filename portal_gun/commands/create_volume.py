from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config
from portal_gun.commands.aws_client import AwsClient
from portal_gun.helpers.pretty_print import print_volume


class CreateVolumeCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'volume'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Perform operations with persistent volumes')
		parser.add_argument('-l', '--list', dest='list', action='store_true', help='List volumes')

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		# Find, parse and validate configs
		print('Checking configuration...')
		config = get_config(self._args)
		print('Done.\n')

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		if self._args.list:
			self.list_volumes(aws)

	def list_volumes(self, aws):
		volumes = aws.get_volumes()
		map(print_volume, volumes)


