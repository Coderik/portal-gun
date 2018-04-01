from __future__ import print_function
import datetime
import time
import sys

import boto3
from fabric.tasks import execute
from fabric.api import env, hide, sudo, run
from fabric.context_managers import prefix

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands.helpers import get_config, get_portal_spec
from portal_gun.commands.aws_client import AwsClient
import portal_gun.aws_helpers as aws_helpers
from portal_gun.commands import common


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)
		self._fabric_retry_limit = 5

	@staticmethod
	def cmd():
		return 'open'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Open portal')
		parser.add_argument('portal', help='Name of portal')

	# TODO: add verbose mode that prints all configs and dry-run mode to check the configs and permissions
	def run(self):
		print('Running `{}` command.\n'.format(self.cmd()))

		# Find, parse and validate configs
		print('Checking configuration...')
		config = get_config(self._args)
		portal_spec, portal_name = get_portal_spec(self._args)
		print('Done.\n')

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		print('Check requested resources:')

		# Get current user
		with pass_step_or_die('Get user identity',
							  'Could not get current user identity'.format(portal_name)):
			user = aws.get_user_identity()

		# Ensure that instance does not yet exist
		with pass_step_or_die('Check already running instances',
							  'Portal `{}` seems to be already opened'.format(portal_name),
							  errors=[RuntimeError]):
			common.check_instance_not_exists(aws, portal_name, user['Arn'])

		# Ensure persistent volumes are available
		with pass_step_or_die('Check volumes availability',
							  'Not all volumes are available',
							  errors=[RuntimeError]):
			volume_ids = [volume_spec['volume_id'] for volume_spec in portal_spec['persistent_volumes']]
			common.check_volumes_availability(aws, volume_ids)

		print('Required resources are available.\n')

		# Make request for Spot instance
		print('Request a Spot instance:')
		request_config = aws_helpers.single_instance_spot_fleet_request(portal_spec, portal_name, user['Arn'])
		response = aws.request_spot_fleet(request_config)
		spot_fleet_request_id = response['SpotFleetRequestId']

		# Wait for spot fleet request to be fulfilled
		print('\tWaiting for the Spot instance to be created...'.expandtabs(4))
		print('\t(usually it takes around a minute, but might take much longer)'.expandtabs(4))
		begin_time = datetime.datetime.now()
		next_time = begin_time
		try:
			while True:
				# Repeat status request every N seconds
				if datetime.datetime.now() > next_time:
					spot_fleet_request = aws.get_spot_fleet_request(spot_fleet_request_id)
					next_time += datetime.timedelta(seconds=5)

				# Compute time spend in waiting
				elapsed = datetime.datetime.now() - begin_time

				# Check request state and activity status
				request_state = spot_fleet_request['SpotFleetRequestState']
				if request_state == 'active':
					spot_request_status = spot_fleet_request['ActivityStatus']
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
		except KeyboardInterrupt:
			print('\nInterrupting...')

			# Cancel spot instance request
			aws.cancel_spot_fleet_request(spot_fleet_request_id)

			print('Spot request has been cancelled.')
			exit()
		print('\nSpot instance is created in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# Get id of the created instance
		spot_fleet_instances = aws.get_spot_fleet_instances(spot_fleet_request_id)
		instance_id = spot_fleet_instances[0]['InstanceId']

		# Get information about the created instance
		instance_info = aws.get_instance(instance_id)

		# Make requests to attach persistent volumes
		print('Requests attachment of persistent volumes:')
		for volume_spec in portal_spec['persistent_volumes']:
			response = aws.attach_volume(instance_id, volume_spec['volume_id'], volume_spec['device'])

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
				volumes = aws.get_volumes_by_id(volume_ids)
				next_time += datetime.timedelta(seconds=1)

			# Compute time spend in waiting
			elapsed = datetime.datetime.now() - begin_time

			if all([volume['Attachments'][0]['State'] == 'attached' for volume in volumes]):
				break
			else:
				states = ['{} - `{}`'.format(volume['VolumeId'], volume['Attachments'][0]['State'])
						  for volume in volumes]
				print('\r\tElapsed {}s. States: {}'.format(elapsed.seconds, ', '.join(states)).expandtabs(4), end='\r')

			sys.stdout.flush()  # ensure stdout is flushed immediately.
			time.sleep(0.5)
		print('\nPersistent volumes are attached in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# Configure ssh connection via fabric
		env.user = portal_spec['spot_instance']['remote_user']
		env.key_filename = [portal_spec['spot_instance']['ssh_key_file']]
		env.hosts = instance_info['PublicDnsName']
		env.connection_attempts = self._fabric_retry_limit

		print('Prepare the instance:')

		# Mount persistent volumes
		for i in range(len(portal_spec['persistent_volumes'])):
			with pass_step_or_die('Mount volume #{}'.format(i),
								  'Could not mount volume',
								  errors=[RuntimeError]):
				volume_spec = portal_spec['persistent_volumes'][i]
				with hide('running', 'stdout'):
					execute(self.mount_volume, volume_spec['device'], volume_spec['mount_point'])

		# TODO: consider importing and executing custom fab tasks instead
		# Install extra python packages, if needed
		if 'extra_python_packages' in portal_spec['spot_instance'] and \
						len(portal_spec['spot_instance']['extra_python_packages']) > 0:
			with pass_step_or_die('Install extra python packages',
								  'Could not install python packages',
								  errors=[RuntimeError]):
				python_packages = portal_spec['spot_instance']['extra_python_packages']
				virtual_env = portal_spec['spot_instance']['python_virtual_env']
				with hide('running', 'stdout'):
					execute(self.install_python_packages, python_packages, virtual_env)

		print('Instance is ready.\n')

		# Print summary
		print('Portal `{}` is now opened.'.format(portal_name))
		print('Summary:')
		print('\tInstance:'.expandtabs(4))
		print('\t\tId:              {}'.format(instance_id).expandtabs(4))
		print('\t\tType:            {}'.format(instance_info['InstanceType']).expandtabs(4))
		print('\t\tPublic IP:       {}'.format(instance_info['PublicIpAddress']).expandtabs(4))
		print('\t\tPublic DNS name: {}'.format(instance_info['PublicDnsName']).expandtabs(4))
		print('\tPersistent volumes:'.expandtabs(4))
		for volume_spec in portal_spec['persistent_volumes']:
			print('\t\t{}: {}'.format(volume_spec['device'], volume_spec['mount_point']).expandtabs(4))
		print('')

		# Print ssh command
		print('Use the following command to connect to the remote machine:')
		print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
										 portal_spec['spot_instance']['remote_user'],
										 instance_info['PublicDnsName']))

	def mount_volume(self, device, mount_point):
		# Ensure volume contains a file system
		out = sudo('file -s {}'.format(device))
		if out == '{}: data':
			raise RuntimeError('There is no file system on the device `{}`'.format(device))

		# Create mount point
		run('mkdir -p {}'.format(mount_point))

		# Mount volume
		sudo('mount {} {}'.format(device, mount_point))

	def install_python_packages(self, packages, virtual_env):
		with prefix('source activate {}'.format(virtual_env)):
			run('pip install {}'.format(' '.join(packages)))
