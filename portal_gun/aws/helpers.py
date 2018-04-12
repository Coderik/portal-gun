import datetime


def to_aws_tags(tags):
	"""
	Convert tags from dictionary to a format expected by AWS:
	[{'Key': key, 'Value': value}]
	:param tags
	:return:
	"""
	return [{'Key': k, 'Value': v} for k, v in tags.iteritems()]


def from_aws_tags(tags):
	"""
	Convert tags from AWS format [{'Key': key, 'Value': value}] to dictionary
	:param tags
	:return:
	"""
	return {tag['Key']: tag['Value'] for tag in tags}


def single_instance_spot_fleet_request(portal_spec, portal_name, user):
	instance_spec = portal_spec['spot_instance']
	fleet_spec = portal_spec['spot_fleet']

	fleet_request_config = {
		'AllocationStrategy': 'lowestPrice',
		'IamFleetRole': fleet_spec['iam_fleet_role'],
		'TargetCapacity': 1,
		'ValidFrom': datetime.datetime.utcnow().isoformat().rsplit('.', 1)[0] + 'Z',
  		'ValidUntil': (datetime.datetime.utcnow() + datetime.timedelta(days=60)).isoformat().rsplit('.', 1)[0] + 'Z',
		'TerminateInstancesWithExpiration': True,
		'Type': 'request',
		'LaunchSpecifications': [
			{
				'ImageId': instance_spec['image_id'],
				'InstanceType': instance_spec['instance_type'],
				'KeyName': instance_spec['key_pair_name'],
				'Placement': {
					'AvailabilityZone': instance_spec['availability_zone']
				},
				'NetworkInterfaces': [{
					'SubnetId': instance_spec['subnet_id'],
					'Groups': [instance_spec['security_group_id']],
					'DeviceIndex': 0
				}],
				'TagSpecifications': [{
					'ResourceType': 'instance',
					'Tags': [
						{'Key': 'portal-name', 'Value': portal_name},
						{'Key': 'created-by', 'Value': user},
					]
				}]
			}
		]
	}

	# Add provided optional fields
	if 'ebs_optimized' in instance_spec:
		fleet_request_config['LaunchSpecifications'][0]['EbsOptimized'] = instance_spec['ebs_optimized']

	return fleet_request_config


def build_instance_launch_spec(instance_spec):
	# Set required fields
	aws_launch_spec = {
		'SecurityGroupIds': [instance_spec['security_group_id']],
		'ImageId': instance_spec['image_id'],
		'InstanceType': instance_spec['instance_type'],
		'KeyName': instance_spec['key_pair_name'],
		'Placement': {
			'AvailabilityZone': instance_spec['availability_zone']
		}
	}

	# Add provided optional fields
	if 'ebs_optimized' in instance_spec:
		aws_launch_spec['EbsOptimized'] = instance_spec['ebs_optimized']

	return aws_launch_spec
