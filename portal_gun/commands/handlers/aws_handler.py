from __future__ import print_function

import datetime
import sys
import time

import portal_gun.providers.aws.helpers as aws_helpers
import portal_gun.fabric as fab
from portal_gun.commands.exceptions import CommandError
from portal_gun.commands.handlers.base_handler import BaseHandler
from portal_gun.configuration.draft import generate_draft
from portal_gun.configuration.schemas import PortalSchema, ComputeSchema
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step
from portal_gun.providers.aws.aws_client import AwsClient
from portal_gun.providers.aws.pretty_print import print_volume


class AwsHandler(BaseHandler):
	def __init__(self, config):
		super(AwsHandler, self).__init__(config)

		self._proper_tag_key = 'dimension'
		self._proper_tag_value = 'C-137'
		self._service_tags = [self._proper_tag_key, 'created-by', 'mount-point']
		self._default_size = 50  # Gb
		self._min_size = 1  # Gb
		self._max_size = 16384  # Gb

	@staticmethod
	def provider_name():
		return 'aws'

	@staticmethod
	def provider_long_name():
		return 'Amazon Web Services'

	@staticmethod
	def generate_portal_spec():
		return generate_draft(PortalSchema(), selectors={ComputeSchema: 'aws'})

	def open_portal(self, portal_spec, portal_name):
		# Create AWS client
		aws = self._create_client()

		# Define shortcuts
		compute_spec = portal_spec['compute']
		instance_spec = compute_spec['instance']
		network_spec = compute_spec['network']
		auth_spec = compute_spec['auth']

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Ensure that instance does not yet exist
			with step('Check already running instances',
					  error_message='Portal `{}` seems to be already opened'.format(portal_name),
					  catch=[RuntimeError]):
				spot_instance = aws.find_spot_instance(portal_name, user['Arn'])

				if spot_instance is not None:
					raise RuntimeError('Instance is already running')

			# Ensure persistent volumes are available
			with step('Check volumes availability', catch=[RuntimeError]):
				volume_ids = [volume_spec['volume_id'] for volume_spec in portal_spec['persistent_volumes']]
				volumes = aws.get_volumes_by_id(volume_ids)

				if not all([volume['State'] == 'available' for volume in volumes]):
					states = ['{} is {}'.format(volume['VolumeId'], volume['State']) for volume in volumes]
					raise RuntimeError('Not all volumes are available: {}'.format(', '.join(states)))

			# If subnet Id is not provided, pick the default subnet of the availability zone
			if 'subnet_id' not in network_spec or not network_spec['subnet_id']:
				with step('Get subnet id', catch=[IndexError, KeyError]):
					subnets = aws.get_subnets(instance_spec['availability_zone'])
					network_spec['subnet_id'] = subnets[0]['SubnetId']

		# Make request for Spot instance
		with print_scope('Requesting a Spot instance of type {}:'.format(instance_spec['type'])):
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
		fab_conn = fab.create_connection(instance_info['PublicDnsName'], auth_spec['user'], auth_spec['identity_file'])

		with print_scope('Preparing the instance:', 'Instance is ready.\n'):
			# Mount persistent volumes
			for i in range(len(portal_spec['persistent_volumes'])):
				with step('Mount volume #{}'.format(i), error_message='Could not mount volume',
						  catch=[RuntimeError]):
					volume_spec = portal_spec['persistent_volumes'][i]

					# Mount volume
					fab.mount_volume(fab_conn, volume_spec['device'], volume_spec['mount_point'],
									 auth_spec['user'], auth_spec['group'])

					# Store extra information in volume's tags
					aws.add_tags(volume_spec['volume_id'], {'mount-point': volume_spec['mount_point']})

			# TODO: consider importing and executing custom fab tasks instead
			# Install extra python packages, if needed
			if 'provision_actions' in compute_spec and len(compute_spec['provision_actions']) > 0:
				for action_spec in compute_spec['provision_actions']:
					if action_spec['name'] == 'install-python-packages':
						virtual_env = action_spec['args']['virtual_env']
						packages = action_spec['args']['packages']
						with step('Install extra python packages', error_message='Could not install python packages',
								  catch=[RuntimeError]):
							fab.install_python_packages(fab_conn, virtual_env, packages)

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
		print('ssh -i "{}" {}@{}'.format(auth_spec['identity_file'],
										 auth_spec['user'],
										 instance_info['PublicDnsName']))

	def close_portal(self, portal_spec, portal_name):
		# Create AWS client
		aws = self._create_client()

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Get spot instance
			with step('Get spot instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				spot_instance = aws.find_spot_instance(portal_name, user['Arn'])

				if spot_instance is None:
					raise RuntimeError('Instance is not running')

			spot_fleet_request_id = \
				filter(lambda tag: tag['Key'] == 'aws:ec2spot:fleet-request-id', spot_instance['Tags'])[0]['Value']

			# Get spot instance
			with step('Get spot request', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				spot_fleet_request = aws.get_spot_fleet_request(spot_fleet_request_id)

				if spot_fleet_request is None:
					raise RuntimeError('Could not find spot instance request')

		# TODO: print fleet and instance statistics

		# Cancel spot instance request
		aws.cancel_spot_fleet_request(spot_fleet_request_id)

		# Clean up volumes' tags
		volume_ids = [volume['Ebs']['VolumeId']
					  for volume in spot_instance['BlockDeviceMappings']
					  if not volume['Ebs']['DeleteOnTermination']]
		aws.remove_tags(volume_ids, 'mount-point')

		print('Portal `{}` has been closed.'.format(portal_name))

	def show_portal_info(self, portal_spec, portal_name):
		# Create AWS client
		aws = self._create_client()

		# Define shortcut
		auth_spec = portal_spec['compute']['auth']

		volumes = []
		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				aws_user = aws.get_user_identity()

			# Get spot instance
			with step('Get spot instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

			# Get persistent volumes, if portal is opened
			if instance_info is not None:
				with step('Get volumes'):
					volume_ids = [volume['Ebs']['VolumeId']
								  for volume in instance_info['BlockDeviceMappings']
								  if not volume['Ebs']['DeleteOnTermination']]
					volumes = aws.get_volumes_by_id(volume_ids)

		# Print status
		if instance_info is not None:
			with print_scope('Summary:', ''):
				print('Name:              {}'.format(portal_name))
				print('Status:            open')

			with print_scope('Instance:', ''):
				print('Id:                {}'.format(instance_info['InstanceId']))
				print('Type:              {}'.format(instance_info['InstanceType']))
				print('Public IP:         {}'.format(instance_info['PublicIpAddress']))
				print('Public DNS name:   {}'.format(instance_info['PublicDnsName']))
				print('User:              {}'.format(auth_spec['user']))

			with print_scope('Persistent volumes:', ''):
				for i in range(len(volumes)):
					volume = volumes[i]
					with print_scope('Volume #{}:'.format(i), ''):
						self._print_volume_info(volume)

			# Print ssh command
			with print_scope('Use the following command to connect to the remote machine:'):
				print('ssh -i "{}" {}@{}'.format(auth_spec['identity_file'],
												 auth_spec['user'],
												 instance_info['PublicDnsName']))
		else:
			with print_scope('Summary:'):
				print('Name:              {}'.format(portal_name))
				print('Status:            close')

	def get_portal_info_field(self, portal_spec, portal_name, field):
		# Define shortcut
		auth_spec = portal_spec['compute']['auth']

		if field == 'name':
			return portal_name
		if field == 'user':
			return auth_spec['user']
		if field == 'key':
			return auth_spec['identity_file']

		# Create AWS client
		aws = self._create_client()

		# Get current user
		aws_user = aws.get_user_identity()

		# Get spot instance
		instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

		if field == 'status':
			return 'open' if instance_info is not None else 'close'

		# If portal is closed, we cannot provide any other information
		if instance_info is None:
			return None

		if field == 'id':
			return instance_info['InstanceId']
		if field == 'type':
			return instance_info['InstanceType']
		if field == 'host':
			return instance_info['PublicDnsName']
		if field == 'ip':
			return instance_info['PublicIpAddress']
		if field == 'remote':
			return '{}@{}'.format(auth_spec['user'], instance_info['PublicDnsName'])

		return None

	def get_ssh_params(self, portal_spec, portal_name):
		# Create AWS client
		aws = self._create_client()

		# Define shortcut
		auth_spec = portal_spec['compute']['auth']

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				aws_user = aws.get_user_identity()

			# Get spot instance
			with step('Get spot instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name)):
				instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])
				if instance_info is None:
					raise CommandError('Portal `{}` does not seem to be opened'.format(portal_name))

		# Return parameters for ssh
		return (auth_spec['identity_file'],
				auth_spec['user'],
				instance_info['PublicDnsName'],
				False)

	def list_volumes(self, args):
		# Create AWS client
		aws = self._create_client()

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			if not args.all:
				# Get current user
				with step('Get user identity'):
					user = aws.get_user_identity()

				# Get list of volumes owned by user
				with step('Get list of proper volumes'):
					volumes = aws.get_volumes(self._get_proper_volume_filter(user))
			else:
				# Get list of all volumes
				with step('Get list of volumes'):
					volumes = aws.get_volumes()

		# Filter tags of every volume
		volumes = (self._filter_tags(volume) for volume in volumes)

		# Pretty print list of volumes
		map(print_volume, volumes)

	def create_volume(self, args):
		# Create AWS client
		aws = self._create_client()

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Ensure that instance does not yet exist
			with step('Get Availability Zones'):
				availability_zones = aws.get_availability_zones()

		print('Creating new persistent volume.')

		# Get properties of the new volume
		name = args.name
		size = args.size
		availability_zone = args.zone
		snapshot_id = args.snapshot

		# Ask for name, if not provided
		if name is None:
			print('Enter name for the new volume (no name by default): ', end='')
			name = raw_input() or None

		# Ask for size, if not provide
		if args.size is None:
			print('Enter size of the new volume in Gb ({}): '.format(self._default_size), end='')
			size = raw_input() or self._default_size
			try:
				size = int(size)
			except ValueError as e:
				raise CommandError('Size has to be an integer.')

		# Check size parameter
		if size < self._min_size:
			raise CommandError('Specified size {}Gb is smaller than the lower limit of {}Gb.'
							   .format(size, self._min_size))
		elif size > self._max_size:
			raise CommandError('Specified size {}Gb is bigger than the upper limit of {}Gb.'
							   .format(size, self._max_size))

		# Ask for availability zone, if not provided
		if availability_zone is None:
			print('Enter availability zone for the new volume ({}): '.format(availability_zones[0]), end='')
			availability_zone = raw_input() or availability_zones[0]

		# Check availability zone
		if availability_zone not in availability_zones:
			raise CommandError('Unexpected availability zone "{}". Available zones are: {}.'
							   .format(availability_zone, ', '.join(availability_zones)))

		# Set tags
		tags = {'Name': name, 'created-by': user['Arn'], self._proper_tag_key: self._proper_tag_value}

		# Add user-specified tags, if provided
		if args.tags is not None:
			tags.update(self._parse_tags(args.tags))

		# Create volume
		volume_id = aws.create_volume(size, availability_zone, tags, snapshot_id)

		print('New persistent volume has been created.\nVolume id: {}'.format(volume_id))

	def update_volume(self, args):
		# Create AWS client
		aws = self._create_client()

		updates = 0

		# Get user tags
		tags = self._parse_tags(args.tags)

		# Add 'Name' tag, if specified
		if args.name is not None:
			tags.update({'Name': args.name})

		# Update tags, if specified
		if len(tags) > 0:
			aws.add_tags(args.volume_id, tags)
			updates += len(tags)

		# Update size, if specified
		if args.size is not None:
			aws.update_volume(args.volume_id, args.size)
			updates += 1

		if updates > 0:
			print('Volume {} is updated.'.format(args.volume_id))
		else:
			print('Nothing to do.')

	def delete_volume(self, args):
		# Create AWS client
		aws = self._create_client()

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Ensure that instance does not yet exist
			with step('Get volume details'):
				volume = aws.get_volumes_by_id(args.volume_id)[0]

		if not self._is_proper_volume(volume, user) and not args.force:
			raise CommandError('Volume {} is not owned by you. Use -f flag to force deletion.'.format(args.volume_id))

		aws.delete_volume(args.volume_id)

		print('Volume {} is deleted.'.format(args.volume_id))

	def _create_client(self):
		assert self._config

		return AwsClient(self._config['access_key'],
						 self._config['secret_key'], self._config['region'])

	def _print_volume_info(self, volume):
		tags = volume['Tags'] if 'Tags' in volume else []

		# Look for specific tags
		name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), '')
		mount_point = next((tag['Value'] for tag in tags if tag['Key'] == 'mount-point'), 'n/a')

		print('Id:            {}'.format(volume['VolumeId']))
		print('Name:          {}'.format(name))
		print('Size:          {}Gb'.format(volume['Size']))
		print('Device:        {}'.format(volume['Attachments'][0]['Device']))
		print('Mount point:   {}'.format(mount_point))

	def _filter_tags(self, volume):
		if 'Tags' in volume:
			volume['Tags'] = [tag for tag in volume['Tags'] if tag['Key'] not in self._service_tags]

		return volume

	def _is_proper_volume(self, volume, user):
		try:
			tags = aws_helpers.from_aws_tags(volume['Tags'])
			return tags[self._proper_tag_key] == self._proper_tag_value and tags['created-by'] == user['Arn']
		except KeyError:
			return False

	def _get_proper_volume_filter(self, user):
		return {'tag:{}'.format(self._proper_tag_key): self._proper_tag_value, 'tag:created-by': user['Arn']}

	def _parse_tags(self, tags):
		"""
		Parse tags from command line arguments.
		:param tags: List of tag args in 'key:value' format.
		:return: Tags in dictionary format
		"""
		return {key_value[0]: key_value[1] for key_value in
				(tag.split(':') for tag in (tags or []))
				if len(key_value) == 2 and len(key_value[0]) > 0 and len(key_value[1]) > 0}
