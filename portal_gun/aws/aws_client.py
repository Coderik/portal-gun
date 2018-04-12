import boto3
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ClientError

from portal_gun.aws.helpers import to_aws_tags
from portal_gun.aws.exceptions import AwsRequestError


class AwsClient(object):
	def __init__(self, access_key, secret_key, region):
		self._access_key = access_key
		self._secret_key = secret_key
		self._region = region
		self._ec2_client = None
		self._sts_client = None

	def get_user_identity(self):
		try:
			response = self.sts_client().get_caller_identity()
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response

	def get_availability_zones(self):
		try:
			response = self.ec2_client().describe_availability_zones()
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		try:
			zones = [zone['ZoneName'] for zone in response['AvailabilityZones'] if zone['State'] == 'available']
		except KeyError as e:
			raise AwsRequestError('Response from AWS has unexpected format: {}.'.format(e.message))

		return zones

	def find_spot_instance(self, portal_name, user):
		# Define filters
		filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
				   {'Name': 'tag:created-by', 'Values': [user]},
				   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]

		try:
			response = self.ec2_client().describe_instances(Filters=filters)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		if len(response['Reservations']) == 0 or len(response['Reservations'][0]['Instances']) == 0:
			return None

		return response['Reservations'][0]['Instances'][0]

	def get_instance(self, instance_id):
		try:
			response = self.ec2_client().describe_instances(InstanceIds=[instance_id])
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		if len(response['Reservations']) == 0 or len(response['Reservations'][0]['Instances']) == 0:
			return None

		return response['Reservations'][0]['Instances'][0]

	def get_spot_fleet_instances(self, spot_fleet_request_id):
		try:
			response = self.ec2_client().describe_spot_fleet_instances(SpotFleetRequestId=spot_fleet_request_id)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response['ActiveInstances']

	def get_spot_fleet_request(self, spot_fleet_request_id):
		try:
			response = self.ec2_client().describe_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id])
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		if len(response['SpotFleetRequestConfigs']) == 0:
			return None

		return response['SpotFleetRequestConfigs'][0]

	def get_volumes_by_id(self, volume_ids):
		"""
		:param volume_ids: One or several volume Ids
		:type volume_ids: string or list
		:return:
		"""
		try:
			response = self.ec2_client().describe_volumes(VolumeIds=AwsClient._as_list(volume_ids))
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response['Volumes']

	def get_volumes(self, filters=None):
		if filters is None:
			filters = {}

		# Convert list of filters to the expected format
		aws_filters = [{'Name': k, 'Values': AwsClient._as_list(v)} for k, v in filters.iteritems()]

		# Make request
		try:
			response = self.ec2_client().describe_volumes(Filters=aws_filters)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response['Volumes']

	def create_volume(self, size, availability_zone, tags=None, snapshot_id=None):
		if tags is None:
			tags = {}
		if snapshot_id is None:
			snapshot_id = ''

		# Convert tags to the expected format
		aws_tags = to_aws_tags(tags)

		# Make request
		try:
			response = self.ec2_client().create_volume(AvailabilityZone=availability_zone,
													   Size=size,
													   VolumeType='gp2',
													   SnapshotId=snapshot_id,
													   TagSpecifications=[{'ResourceType': 'volume', 'Tags': aws_tags}])
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response['VolumeId']

	def update_volume(self, volume_id, size):
		try:
			response = self.ec2_client().modify_volume(VolumeId=volume_id,
													   Size=size)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')
		except ClientError as e:
			raise AwsRequestError(e.message)

		self._check_status_code(response)

		return response

	def attach_volume(self, instance_id, volume_id, device):
		try:
			response = self.ec2_client().attach_volume(InstanceId=instance_id,
													   VolumeId=volume_id,
													   Device=device)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response

	def delete_volume(self, volume_id):
		try:
			response = self.ec2_client().delete_volume(VolumeId=volume_id)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')
		except ClientError as e:
			raise AwsRequestError(e.message)

		self._check_status_code(response)

		return response

	def add_tags(self, resource_id, tags):
		"""
		Add or overwrite tags for an EC2 resource (e.g. an instance or a volume).
		:param resource_id:
		:param tags: dict
		:return:
		"""
		# Convert tags to the expected format
		aws_tags = to_aws_tags(tags)

		try:
			response = self.ec2_client().create_tags(Resources=[resource_id], Tags=aws_tags)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return True

	def request_spot_fleet(self, config):
		try:
			response = self.ec2_client().request_spot_fleet(SpotFleetRequestConfig=config)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		return response

	def cancel_spot_fleet_request(self, spot_fleet_request_id):
		try:
			response = self.ec2_client().cancel_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id],
																	TerminateInstances=True)
		except EndpointConnectionError as e:
			raise AwsRequestError('Could not make request to AWS.')

		self._check_status_code(response)

		# TODO: check the response to make sure request was canceled
		return True

	def ec2_client(self):
		if self._ec2_client is None:
			self._ec2_client = boto3.client('ec2',
											self._region,
											aws_access_key_id=self._access_key,
											aws_secret_access_key=self._secret_key)

		return self._ec2_client

	def sts_client(self):
		if self._sts_client is None:
			self._sts_client = boto3.client('sts',
											aws_access_key_id=self._access_key,
											aws_secret_access_key=self._secret_key)

		return self._sts_client

	@staticmethod
	def _as_list(x):
		"""
		Ensure that argument is a list
		:param x: Individual element or list
		:return: List
		:rtype: list
		"""
		return x if type(x) == list else [x]

	@staticmethod
	def _check_status_code(response):
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			raise AwsRequestError('Request to AWS failed with status code {}.'.format(status_code))
