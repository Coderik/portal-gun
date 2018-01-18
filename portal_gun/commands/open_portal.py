from os import path
import json

import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.validation import validate_portal_spec, validate_config


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		# Get portal name
		if len(self._args.props) == 0:
			exit('\tNo portal name was provided.')

		portal_name = self._args.props[0]

		# Ensure file with this name does not exist
		file_name = '{}.json'.format(portal_name)
		if not path.exists(file_name):
			exit('\tCould not find portal specification `{}`.'.format(file_name))

		# Parse portal spec
		try:
			with open(file_name) as spec_file:
				portal_spec = json.load(spec_file)
		except IOError as e:
			exit('\tCould not read portal specification file: {}'.format(e))
		except json.decoder.JSONDecodeError as e:
			exit('\tCould not parse portal specification file: {}'.format(e))

		error = validate_portal_spec(portal_spec)
		if error is not None:
			exit('\tPortal specification is not valid: {}'.format(error))

		# Parse global config
		try:
			with open(self._args.config) as config_file:
				config = json.load(config_file)
		except IOError as e:
			exit('\tCould not read config file: {}'.format(e))
		except json.decoder.JSONDecodeError as e:
			exit('\tCould not parse config file: {}'.format(e))

		error = validate_config(config)
		if error is not None:
			exit('\tConfig is not valid: {}'.format(error))

		ec2_client = boto3.client('ec2',
								  config['aws_region'],
								  aws_access_key_id=config['aws_access_key'],
								  aws_secret_access_key=config['aws_secret_key'])

		# Make a request for Spot instance
		launch_spec = {
			'SecurityGroups': [portal_spec['spot_instance_spec']['security_group']],
			'EbsOptimized': portal_spec['spot_instance_spec']
		}
		response = ec2_client.request_spot_instances(InstanceCount=1)

		print('Done')

	@staticmethod
	def cmd():
		return 'open'
