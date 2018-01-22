from __future__ import print_function
import datetime
import time
import sys

import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands.helpers import run_preflight_steps
import portal_gun.aws_helpers as aws_helpers


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'open'

	# TODO: add verbose mode that prints all configs and dry-run mode to check the configs and permissions
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

		print('Check requested resources:')

		# Ensure that instance does not yet exist
		with pass_step_or_die('Check already running instances',
							  'Portal `{}` seems to be already opened'.format(portal_name),
							  errors=[RuntimeError]):
			self.check_instance_not_exists(ec2_client, portal_name, 'user')

		# Ensure persistent volumes are available
		with pass_step_or_die('Check volumes availability',
							  'Not all volumes are available',
							  errors=[RuntimeError]):
			volume_ids = [volume_spec['volume_id'] for volume_spec in portal_spec['persistent_volumes']]
			self.check_volumes_availability(ec2_client, volume_ids)

		print('Required resources are available.\n')

		# Make request for Spot instance
		print('Request a Spot instance:')
		request_config = aws_helpers.single_instance_spot_fleet_request(portal_spec, portal_name, 'user')
		response = ec2_client.request_spot_fleet(SpotFleetRequestConfig=request_config)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		spot_fleet_request_id = response['SpotFleetRequestId']

		# Wait for spot fleet request to be fulfilled
		print('\tWaiting for the Spot instance to be created...'.expandtabs(4))
		begin_time = datetime.datetime.now()
		next_time = begin_time
		while True:
			# Repeat status request every N seconds
			if datetime.datetime.now() > next_time:
				response = ec2_client.describe_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id])
				next_time += datetime.timedelta(seconds=5)

			# Compute time spend in waiting
			elapsed = datetime.datetime.now() - begin_time

			# Check request state and activity status
			request_state = response['SpotFleetRequestConfigs'][0]['SpotFleetRequestState']
			if request_state == 'active':
				spot_request_status = response['SpotFleetRequestConfigs'][0]['ActivityStatus']
				if spot_request_status == 'fulfilled':
					break
				else:
					print('\r\tElapsed {}s. Spot request is {} and has status `{}`'
						  .format(elapsed.seconds, request_state, spot_request_status).expandtabs(4), end='\r')
			else:
				print('\r\tElapsed {}s. Spot request is {}'.format(elapsed.seconds, request_state).expandtabs(4),
					  end='\r')

			sys.stdout.flush()  # ensure stdout is flushed immediately.
			time.sleep(0.5)
		print('\nSpot instance is created in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		response = ec2_client.describe_spot_fleet_instances(SpotFleetRequestId=spot_fleet_request_id)

		instance_id = response['ActiveInstances'][0]['InstanceId']

		# Get information about the instance
		response = ec2_client.describe_instances(InstanceIds=[instance_id])

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		instance_info = response['Reservations'][0]['Instances'][0]

		print('Instance info:')
		print('\tId:              {}'.format(instance_id).expandtabs(4))
		print('\tPublic IP:       {}'.format(instance_info['PublicIpAddress']).expandtabs(4))
		print('\tPublic DNS name: {}'.format(instance_info['PublicDnsName']).expandtabs(4))
		print('')

		# Make requests to attach persistent volumes
		print('Requests attachment of persistent volumes:')
		for volume_spec in portal_spec['persistent_volumes']:
			response = ec2_client.attach_volume(InstanceId=instance_id,
												VolumeId=volume_spec['volume_id'],
												Device=volume_spec['device'])

			# Check status code
			if response['State'] not in ['attaching', 'attached']:
				exit('Could not attach persistent volume `{}`'.format(volume_spec['volume_id']))

		# Wait for persistent volumes to be attached
		print('\tWaiting for the persistent volumes to be attached...'.expandtabs(4))
		begin_time = datetime.datetime.now()
		next_time = begin_time
		while True:
			# Repeat status request every N seconds
			if datetime.datetime.now() > next_time:
				response = ec2_client.describe_volumes(VolumeIds=volume_ids)
				next_time += datetime.timedelta(seconds=1)

			# Compute time spend in waiting
			elapsed = datetime.datetime.now() - begin_time

			if all([volume['Attachments'][0]['State'] == 'attached' for volume in response['Volumes']]):
				break
			else:
				states = ['{} - `{}`'.format(volume['VolumeId'], volume['Attachments'][0]['State'])
						  for volume in response['Volumes']]
				print('\r\tElapsed {}s. States: {}'.format(elapsed.seconds, ', '.join(states)).expandtabs(4), end='\r')

			sys.stdout.flush()  # ensure stdout is flushed immediately.
			time.sleep(0.5)
		print('\nPersistent volumes are attached in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# TODO: ssh part
		# - check filesystem
		# - create folder
		# - mount volume
		# - install extra packages in virtual env
		# - print ssh command

		print('Done')

	def check_instance_not_exists(self, ec2_client, portal_name, user):
		# Make request
		filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
				   {'Name': 'tag:created-by', 'Values': [user]},
				   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
		response = ec2_client.describe_instances(Filters=filters)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if len(response['Reservations']) != 0:
			raise RuntimeError('Instance is already running')

	def check_volumes_availability(self, ec2_client, volume_ids):
		# Make request
		response = ec2_client.describe_volumes(VolumeIds=volume_ids)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if not all([volume['State'] == 'available' for volume in response['Volumes']]):
			states = ['{} - `{}`'.format(volume['VolumeId'], volume['State']) for volume in response['Volumes']]
			raise RuntimeError('States: {}'.format(', '.join(states)))
