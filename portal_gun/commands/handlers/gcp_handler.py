from __future__ import print_function

import datetime
import sys
import time

from portal_gun.configuration.draft import generate_draft
from portal_gun.configuration.schemas import PortalSchema, ComputeSchema
import portal_gun.providers.gcp.helpers as gcp_helpers
import portal_gun.ssh_ops as ssh
from portal_gun.commands.exceptions import CommandError
from portal_gun.commands.handlers.base_handler import BaseHandler
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step
from portal_gun.providers.gcp.gcp_client import GcpClient
from portal_gun.providers.gcp.pretty_print import print_volume


class GcpHandler(BaseHandler):
	def __init__(self, config):
		super(GcpHandler, self).__init__(config)

	@staticmethod
	def provider_name():
		return 'gcp'

	@staticmethod
	def provider_long_name():
		return 'Google Cloud Platform'

	@staticmethod
	def generate_portal_spec():
		return generate_draft(PortalSchema(), selectors={ComputeSchema: 'gcp'})

	def open_portal(self, portal_spec, portal_name):
		# Create GCP client
		gcp = self._create_client()

		# Define shortcuts
		compute_spec = portal_spec['compute']
		instance_spec = compute_spec['instance']
		# network_spec = compute_spec['network']
		auth_spec = compute_spec['auth']

		with print_scope('Retrieving data from GCP:', 'Done.\n'):
			# TODO: Retrieving data from GCP
			pass

		# Make request for instance
		with print_scope('Requesting an instance:'):
			instance_name = gcp_helpers.get_instance_name(portal_spec, portal_name)
			instance_props = gcp_helpers.build_instance_props(portal_spec, instance_name)
			operation = gcp.request_instance(instance_props)
			operation_name = operation['name']

			# Wait for spot fleet request to be fulfilled
			print('Waiting for the instance to be created...')
			print('(usually it takes less than a minute, but might take much longer)')
			begin_time = datetime.datetime.now()
			next_time = begin_time
			try:
				while True:
					# Repeat status request every N seconds
					if datetime.datetime.now() > next_time:
						operation = gcp.get_operation(operation_name)
						next_time += datetime.timedelta(seconds=5)

					# Compute time spend in waiting
					elapsed = datetime.datetime.now() - begin_time

					# Check request state and activity status
					request_state = operation['status']
					if request_state == 'DONE':
						break
					else:
						print('Elapsed {}s. Instance request is {}'
							  .format(elapsed.seconds, request_state), end='\r')

					sys.stdout.flush()  # ensure stdout is flushed immediately.
					time.sleep(0.5)
			except KeyboardInterrupt:
				print('\n')
				print('Interrupting...')

				# Cancel spot instance request
				gcp.cancel_instance_request(instance_name)

				raise CommandError('Instance request has been cancelled.')
		print('\nInstance is created in {} seconds.\n'.format((datetime.datetime.now() - begin_time).seconds))

		# Get information about the created instance
		instance_info = gcp.get_instance(instance_name)

		public_ip = instance_info['networkInterfaces'][0]['accessConfigs'][0]['natIP']
		public_dns = public_ip

		# Configure ssh connection via fabric
		ssh.configure(auth_spec['private_ssh_key'], auth_spec['user'], public_dns, disable_known_hosts=True)

		with print_scope('Preparing the instance:', 'Instance is ready.\n'):
			# Mount persistent volumes
			for i in range(len(portal_spec['persistent_volumes'])):
				with step('Mount volume #{}'.format(i), error_message='Could not mount volume',
						  catch=[RuntimeError]):
					volume_spec = portal_spec['persistent_volumes'][i]

					# Mount volume
					ssh.mount_volume(volume_spec['device'], volume_spec['mount_point'],
									 auth_spec['user'], auth_spec['group'])

			# TODO: consider importing and executing custom fab tasks instead
			# Install extra python packages, if needed
			if 'provision_actions' in compute_spec and len(compute_spec['provision_actions']) > 0:
				for action_spec in compute_spec['provision_actions']:
					if action_spec['name'] == 'install-python-packages':
						virtual_env = action_spec['args']['virtual_env']
						packages = action_spec['args']['packages']
						with step('Install extra python packages', error_message='Could not install python packages',
								  catch=[RuntimeError]):
							ssh.install_python_packages(virtual_env, packages)

		# Print summary
		print('Portal `{}` is now opened.'.format(portal_name))
		with print_scope('Summary:', ''):
			with print_scope('Instance:'):
				print('Id:              {}'.format(instance_info['id']))
				print('Name:            {}'.format(instance_name))
				# print('Type:            {}'.format(instance_info['InstanceType']))
				print('Public IP:       {}'.format(public_ip))
				print('Public DNS name: {}'.format(public_dns))
			with print_scope('Persistent volumes:'):
				for volume_spec in portal_spec['persistent_volumes']:
					print('{}: {}'.format(volume_spec['device'], volume_spec['mount_point']))

		# Print ssh command
		print('Use the following command to connect to the remote machine:')
		print('ssh -i "{}" {}@{}'.format(auth_spec['private_ssh_key'],
										 auth_spec['user'],
										 public_dns))

	def close_portal(self, portal_spec, portal_name):
		raise NotImplementedError('Every subclass of BaseHandler should implement close_portal() method.')

	def show_portal_info(self, portal_spec, portal_name):
		raise NotImplementedError('Every subclass of BaseHandler should implement show_portal_info() method.')

	def get_portal_info_field(self, portal_spec, portal_name, field):
		raise NotImplementedError('Every subclass of BaseHandler should implement get_portal_info_field() method.')

	def get_ssh_params(self, portal_spec, portal_name):
		# Create GCP client
		gcp = self._create_client()

		# Define shortcut
		auth_spec = portal_spec['compute']['auth']

		with print_scope('Retrieving data from GCP:', 'Done.\n'):
			# Get current user
			# with step('Get user identity'):
			# 	aws_user = aws.get_user_identity()

			# Get spot instance
			with step('Get instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name)):
				instance_name = gcp_helpers.get_instance_name(portal_spec, portal_name)
				instance_info = gcp.get_instance(instance_name)
				if instance_info is None:
					raise CommandError('Portal `{}` does not seem to be opened'.format(portal_name))

		public_ip = instance_info['networkInterfaces'][0]['accessConfigs'][0]['natIP']

		# Return parameters for ssh
		return (auth_spec['private_ssh_key'],
				auth_spec['user'],
				public_ip,
				True)

	def list_volumes(self, args):
		# Create GCP client
		gcp = self._create_client()

		volumes = gcp.get_volumes()

		# Pretty print list of volumes
		map(print_volume, volumes)

	def create_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement create_volume() method.')

	def update_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement update_volume() method.')

	def delete_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement delete_volume() method.')

	def _create_client(self):
		assert self._config

		return GcpClient(self._config['service_account_file'], self._config['project'], self._config['region'])
