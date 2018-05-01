from __future__ import print_function

from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands import common
from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.helpers import get_config, get_portal_spec
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step


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
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Get spot instance
			with step('Get spot instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				spot_instance = common.get_spot_instance(aws, portal_name, user['Arn'])

			spot_fleet_request_id = \
				filter(lambda tag: tag['Key'] == 'aws:ec2spot:fleet-request-id', spot_instance['Tags'])[0]['Value']

			# Get spot instance
			with step('Get spot request', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				spot_fleet_request = common.get_spot_fleet_request(aws, spot_fleet_request_id)

		# TODO: print fleet and instance statistics

		# Cancel spot instance request
		aws.cancel_spot_fleet_request(spot_fleet_request_id)

		# Clean up volumes' tags
		volume_ids = [volume['Ebs']['VolumeId']
					  for volume in spot_instance['BlockDeviceMappings']
					  if not volume['Ebs']['DeleteOnTermination']]
		aws.remove_tags(volume_ids, 'mount-point')

		print('Portal `{}` has been closed.'.format(portal_name))
