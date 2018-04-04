from __future__ import print_function

from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands import common
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config, get_portal_spec
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
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
		print('Running `{}` command.\n'.format(self.cmd()))

		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with pass_step_or_die('Get user identity',
								  'Could not get current user identity'):
				user = aws.get_user_identity()

			# Get spot instance
			with pass_step_or_die('Get spot instance',
								  'Portal `{}` does not seem to be opened'.format(portal_name),
								  errors=[RuntimeError]):
				spot_instance = common.get_spot_instance(aws, portal_name, user['Arn'])

			spot_fleet_request_id = \
				filter(lambda tag: tag['Key'] == 'aws:ec2spot:fleet-request-id', spot_instance['Tags'])[0]['Value']

			# Get spot instance
			with pass_step_or_die('Get spot request',
								  'Portal `{}` does not seem to be opened'.format(portal_name),
								  errors=[RuntimeError]):
				spot_fleet_request = common.get_spot_fleet_request(aws, spot_fleet_request_id)

		# TODO: print fleet and instance statistics

		# Cancel spot instance request
		aws.cancel_spot_fleet_request(spot_fleet_request_id)

		print('Portal `{}` has been closed.'.format(portal_name))
