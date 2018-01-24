import boto3


def get_user_identity(aws_access_key, aws_secret_key):
	# Create STS client
	sts_client = boto3.client('sts',
							  aws_access_key_id=aws_access_key,
							  aws_secret_access_key=aws_secret_key)

	response = sts_client.get_caller_identity()

	# Check status code
	status_code = response['ResponseMetadata']['HTTPStatusCode']
	if status_code != 200:
		exit('Error: request failed with status code {}.'.format(status_code))

	return response


def get_spot_instance(ec2_client, portal_name, user):
	# Make request
	filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
			   {'Name': 'tag:created-by', 'Values': [user]},
			   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
	response = ec2_client.describe_instances(Filters=filters)

	# Check status code
	status_code = response['ResponseMetadata']['HTTPStatusCode']
	if status_code != 200:
		exit('Error: request failed with status code {}.'.format(status_code))

	if len(response['Reservations']) == 0:
		raise RuntimeError('Instance is not running')

	return response['Reservations'][0]['Instances'][0]


def get_spot_fleet_request(ec2_client, spot_fleet_request_id):
	# Make request
	response = ec2_client.describe_spot_fleet_requests(SpotFleetRequestIds=[spot_fleet_request_id])

	# Check status code
	status_code = response['ResponseMetadata']['HTTPStatusCode']
	if status_code != 200:
		exit('Error: request failed with status code {}.'.format(status_code))

	if len(response['SpotFleetRequestConfigs']) == 0:
		raise RuntimeError('Could not find spot instance request')

	return response['SpotFleetRequestConfigs'][0]


def check_instance_not_exists(ec2_client, portal_name, user):
	# Make request
	filters = [{'Name': 'tag:portal-name', 'Values': [portal_name]},
			   {'Name': 'tag:opened-by', 'Values': [user]},
			   {'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
	response = ec2_client.describe_instances(Filters=filters)

	# Check status code
	status_code = response['ResponseMetadata']['HTTPStatusCode']
	if status_code != 200:
		exit('Error: request failed with status code {}.'.format(status_code))

	if len(response['Reservations']) != 0:
		raise RuntimeError('Instance is already running')


def check_volumes_availability(ec2_client, volume_ids):
	# Make request
	response = ec2_client.describe_volumes(VolumeIds=volume_ids)

	# Check status code
	status_code = response['ResponseMetadata']['HTTPStatusCode']
	if status_code != 200:
		exit('Error: request failed with status code {}.'.format(status_code))

	if not all([volume['State'] == 'available' for volume in response['Volumes']]):
		states = ['{} is {}'.format(volume['VolumeId'], volume['State']) for volume in response['Volumes']]
		raise RuntimeError(', '.join(states))