import boto3


class AwsClient(object):
	def __init__(self, access_key, secret_key, region):
		self._access_key = access_key
		self._secret_key = secret_key
		self._region = region
		self._ec2_client = None
		self._sts_client = None

	def get_user_identity(self):
		# Mare request
		response = self.sts_client().get_caller_identity()

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		return response

	def find_spot_instance(self, portal_name, user):
		# Make request
		filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
				   {'Name': 'tag:created-by', 'Values': [user]},
				   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
		response = self.ec2_client().describe_instances(Filters=filters)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if len(response['Reservations']) == 0 or len(response['Reservations'][0]['Instances']) == 0:
			return None

		return response['Reservations'][0]['Instances'][0]

	def get_instance(self, instance_id):
		# Make request
		response = self.ec2_client().describe_instances(InstanceIds=[instance_id])

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		if len(response['Reservations']) == 0 or len(response['Reservations'][0]['Instances']) == 0:
			return None

		return response['Reservations'][0]['Instances'][0]

	def get_spot_fleet_instances(self, spot_fleet_request_id):
		response = self.ec2_client().describe_spot_fleet_instances(SpotFleetRequestId=spot_fleet_request_id)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		return response['ActiveInstances']

	def get_spot_fleet_request(self, spot_fleet_request_id):
		# Make request
		response = self.ec2_client().describe_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id])

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		if len(response['SpotFleetRequestConfigs']) == 0:
			return None

		return response['SpotFleetRequestConfigs'][0]

	def get_volumes(self, volume_ids):
		# Make request
		response = self.ec2_client().describe_volumes(VolumeIds=volume_ids)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		return response['Volumes']

	def attach_volume(self, instance_id, volume_id, device):
		response = self.ec2_client().attach_volume(InstanceId=instance_id,
												   VolumeId=volume_id,
												   Device=device)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}.'.format(status_code))

		return response

	def request_spot_fleet(self, config):
		response = self.ec2_client().request_spot_fleet(SpotFleetRequestConfig=config)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

		return response

	def cancel_spot_fleet_request(self, spot_fleet_request_id):
		response = self.ec2_client().cancel_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id],
																TerminateInstances=True)

		# Check status code
		status_code = response['ResponseMetadata']['HTTPStatusCode']
		if status_code != 200:
			exit('Error: request failed with status code {}'.format(status_code))

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
