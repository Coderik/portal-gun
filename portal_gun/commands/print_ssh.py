from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.commands.aws_client import AwsClient
from portal_gun.context_managers.no_print import NoPrint


class PrintSshCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'ssh'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Print ssh command to connect to the remote instance')
		parser.add_argument('portal', help='name of portal')

	def run(self):
		# Find, parse and validate configs
		with NoPrint():
			config, portal_spec, portal_name = run_preflight_steps(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		# Get current user
		user = aws.get_user_identity()

		# Get spot instance
		instance_info = aws.find_spot_instance(portal_name, user['Arn'])

		# Print ssh command
		if instance_info is not None:
			print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
											 portal_spec['spot_instance']['remote_user'],
											 instance_info['PublicDnsName']))
