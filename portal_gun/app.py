import boto3

from portal_gun.configuration.validation import validate_config
from portal_gun.configuration.exceptions import ConfigValidationError


class App(object):
	def __init__(self, logger):
		self._logger = logger
		self._config = {}
		self._ec2_client = None
		self._spot_instance_spec = {}

	def configure(self, config):
		self._config = config

		try:
			validate_config(config)
		except ConfigValidationError as e:
			self._logger.error('Config is not valid: {}.'.format(e.message))
			return False

		self._spot_instance_spec = config['spot_instance_spec']

		self._ec2_client = boto3.client('ec2',
										config['aws_region'],
										aws_access_key_id=config['aws_access_key'],
										aws_secret_access_key=config['aws_secret_key'])

		return True

	def run(self):
		# Make a request for Spot instance
		launch_spec = {
			'SecurityGroups': [self._spot_instance_spec['security_group']],
			'EbsOptimized': self._spot_instance_spec['ebs_optimized']
		}
		response = self._ec2_client.request_spot_instances(InstanceCount=1)
