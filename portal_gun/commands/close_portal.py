from __future__ import print_function

import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands.helpers import run_preflight_steps


class ClosePortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'close'

	def run(self):
		print('Running `{}` command.\n'.format(self.cmd()))
		print('Make preflight checks:')

		config, portal_spec, portal_name = run_preflight_steps(self._args)

		print('Preflight checks are complete.\n')

		# Create EC2 client
		ec2_client = boto3.client('ec2',
								  config['aws_region'],
								  aws_access_key_id=config['aws_access_key'],
								  aws_secret_access_key=config['aws_secret_key'])

		# TODO: get current user name

		print('Retrieve associated resources:')

		# Get spot instance
		with pass_step_or_die('Spot instance',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			spot_instance = self.get_spot_instance(ec2_client, portal_name, 'user')

		spot_fleet_request_id = \
			filter(lambda tag: tag['Key'] == 'aws:ec2spot:fleet-request-id', spot_instance['Tags'])[0]['Value']

		# Get spot instance
		with pass_step_or_die('Spot instance request',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			spot_fleet_request = self.get_spot_fleet_request(ec2_client, spot_fleet_request_id)

		print('Done.\n')

		# TODO: print fleet and instance statistics

		# Cancel spot instance request
		response = ec2_client.cancel_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id],
														 TerminateInstances=True)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		# TODO: check the response to make sure request was canceled

		print('Portal `{}` has been closed.'.format(portal_name))

	def get_spot_instance(self, ec2_client, portal_name, user):
		# Make request
		filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
				   {'Name': 'tag:created-by', 'Values': [user]},
				   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
		response = ec2_client.describe_instances(Filters=filters)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if len(response['Reservations']) == 0:
			raise RuntimeError('Instance is not running')

		return response['Reservations'][0]['Instances'][0]

	def get_spot_fleet_request(self, ec2_client, spot_fleet_request_id):
		# Make request
		response = ec2_client.describe_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id])

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if len(response['SpotFleetRequestConfigs']) == 0:
			raise RuntimeError('Could not find spot instance request')

		return response['SpotFleetRequestConfigs'][0]
