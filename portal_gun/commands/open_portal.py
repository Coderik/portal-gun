from os import path
import json
from json.decoder import JSONDecodeError

import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.validation import validate_portal_spec, validate_config
from portal_gun.context_managers.pass_check_or_die import pass_check_or_die
from portal_gun.configuration.exceptions import ConfigValidationError


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		print('\tWarming up...')

		# Parse global config
		with pass_check_or_die('Parse config file', 'Could not parse config file', errors=[IOError, JSONDecodeError]):
			with open(self._args.config) as config_file:
				config = json.load(config_file)

		# Validate global config
		with pass_check_or_die('Validate config', 'Config is not valid', errors=[ConfigValidationError]):
			validate_config(config)

		# Get portal name and portal spec filename
		with pass_check_or_die('Check portal name', 'No portal name was provided'):
			portal_name = self._args.props[0]
			spec_filename = '{}.json'.format(portal_name)

		# Ensure spec file exists
		with pass_check_or_die('Locate portal specification file',
							   'Could not find portal specification file `{}`.'.format(spec_filename)):
			if not path.exists(spec_filename):
				raise Exception()

		# Parse portal spec file
		with pass_check_or_die('Parse portal specification file', 'Could not parse portal specification file',
							   errors=[IOError, json.decoder.JSONDecodeError]):
			with open(spec_filename) as spec_file:
				portal_spec = json.load(spec_file)

		# Validate portal spec
		with pass_check_or_die('Validate portal specification', 'Portal specification is not valid',
							   errors=[ConfigValidationError]):
			validate_portal_spec(portal_spec)

		ec2_client = boto3.client('ec2',
								  config['aws_region'],
								  aws_access_key_id=config['aws_access_key'],
								  aws_secret_access_key=config['aws_secret_key'])

		# Make a request for Spot instance
		launch_spec = {
			'SecurityGroups': [portal_spec['spot_instance_spec']['security_group']],
			'EbsOptimized': portal_spec['spot_instance_spec']
		}
		# response = ec2_client.request_spot_instances(InstanceCount=1)

		print('Done')

	@staticmethod
	def cmd():
		return 'open'
