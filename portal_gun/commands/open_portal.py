from __future__ import print_function

import datetime
import sys
import time

from fabric.api import env, hide, sudo, run
from fabric.context_managers import prefix
from fabric.tasks import execute

import portal_gun.aws.helpers as aws_helpers
from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands import common
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.exceptions import CommandError
from portal_gun.configuration.helpers import get_config, get_portal_spec
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step


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

			# Ensure that instance does not yet exist
			with step('Check already running instances',
					  error_message='Portal `{}` seems to be already opened'.format(portal_name),
					  catch=[RuntimeError]):
				common.check_instance_not_exists(aws, portal_name, user['Arn'])

			# Ensure persistent volumes are available
			with step('Check volumes availability', catch=[RuntimeError]):
				volume_ids = [volume_spec['volume_id'] for volume_spec in portal_spec['persistent_volumes']]
				common.check_volumes_availability(aws, volume_ids)

		# Make request for Spot instance
		instance_type = portal_spec['spot_instance']['instance_type']
		with print_scope('Requesting a Spot instance of type {}:'.format(instance_type)):
			request_config = aws_helpers.single_instance_spot_fleet_request(portal_spec, portal_name, user['Arn'])
			response = aws.request_spot_fleet(request_config)
			spot_fleet_request_id = response['SpotFleetRequestId']

			# Wait for spot fleet request to be fulfilled
			print('Waiting for the Spot instance to be created...')
			print('(usually it takes around a minute, but might take much longer)')
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
							print('Elapsed {}s. Spot request is {} and has status `{}`'
								  .format(elapsed.seconds, request_state, spot_request_status), end='\r')
					else:
						print('Elapsed {}s. Spot request is {}'.format(elapsed.seconds, request_state), end='\r')

					sys.stdout.flush()  # ensure stdout is flushed immediately.
					time.sleep(0.5)
			except KeyboardInterrupt:
				print('\n')
				print('Interrupting...')

				# Cancel spot instance request
				aws.cancel_spot_fleet_request(spot_fleet_request_id)

				raise CommandError('Spot request has been cancelled.')
		print('\nSpot instance is created in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# Get id of the created instance
		spot_fleet_instances = aws.get_spot_fleet_instances(spot_fleet_request_id)
		instance_id = spot_fleet_instances[0]['InstanceId']

		# Get information about the created instance
		instance_info = aws.get_instance(instance_id)

		# Make requests to attach persistent volumes
		with print_scope('Attaching persistent volumes:'):
			for volume_spec in portal_spec['persistent_volumes']:
				response = aws.attach_volume(instance_id, volume_spec['volume_id'], volume_spec['device'])

				# Check status code
				if response['State'] not in ['attaching', 'attached']:
					raise CommandError('Could not attach persistent volume `{}`'.format(volume_spec['volume_id']))

			# Wait for persistent volumes to be attached
			print('Waiting for the persistent volumes to be attached...')
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
					print('Elapsed {}s. States: {}'.format(elapsed.seconds, ', '.join(states)), end='\r')

				sys.stdout.flush()  # ensure stdout is flushed immediately.
				time.sleep(0.5)
		print('\nPersistent volumes are attached in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# Configure ssh connection via fabric
		env.user = portal_spec['spot_instance']['remote_user']
		env.key_filename = [portal_spec['spot_instance']['ssh_key_file']]
		env.hosts = instance_info['PublicDnsName']
		env.connection_attempts = self._fabric_retry_limit

		with print_scope('Preparing the instance:', 'Instance is ready.\n'):
			# Mount persistent volumes
			for i in range(len(portal_spec['persistent_volumes'])):
				with step('Mount volume #{}'.format(i), error_message='Could not mount volume', catch=[RuntimeError]):
					volume_spec = portal_spec['persistent_volumes'][i]

					# Mount volume
					with hide('running', 'stdout'):
						execute(self.mount_volume, volume_spec['device'], volume_spec['mount_point'])

					# Store extra information in volume's tags
					aws.add_tags(volume_spec['volume_id'], {'mount-point': volume_spec['mount_point']})

			# TODO: consider importing and executing custom fab tasks instead
			# Install extra python packages, if needed
			if 'extra_python_packages' in portal_spec['spot_instance'] and \
							len(portal_spec['spot_instance']['extra_python_packages']) > 0:
				with step('Install extra python packages', error_message='Could not install python packages',
						  catch=[RuntimeError]):
					python_packages = portal_spec['spot_instance']['extra_python_packages']
					virtual_env = portal_spec['spot_instance']['python_virtual_env']
					with hide('running', 'stdout'):
						execute(self.install_python_packages, python_packages, virtual_env)

		# Print summary
		print('Portal `{}` is now opened.'.format(portal_name))
		with print_scope('Summary:', ''):
			with print_scope('Instance:'):
				print('Id:              {}'.format(instance_id))
				print('Type:            {}'.format(instance_info['InstanceType']))
				print('Public IP:       {}'.format(instance_info['PublicIpAddress']))
				print('Public DNS name: {}'.format(instance_info['PublicDnsName']))
			with print_scope('Persistent volumes:'):
				for volume_spec in portal_spec['persistent_volumes']:
					print('{}: {}'.format(volume_spec['device'], volume_spec['mount_point']))

		# Print ssh command
		print('Use the following command to connect to the remote machine:')
		print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
										 portal_spec['spot_instance']['remote_user'],
										 instance_info['PublicDnsName']))

	def mount_volume(self, device, mount_point):
		# Ensure volume contains a file system
		out = sudo('file -s {}'.format(device))
		if out == '{}: data'.format(device):
			sudo('mkfs -t ext4 {}'.format(device))

		# Create mount point
		run('mkdir -p {}'.format(mount_point))

		# Mount volume
		sudo('mount {} {}'.format(device, mount_point))

	def install_python_packages(self, packages, virtual_env):
		with prefix('source activate {}'.format(virtual_env)):
			run('pip install {}'.format(' '.join(packages)))
