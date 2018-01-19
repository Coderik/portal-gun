def single_instance_spot_fleet_request(portal_spec):
	instance_spec = portal_spec['spot_instance']
	fleet_spec = portal_spec['spot_fleet']

	fleet_request_config = {
		'AllocationStrategy': 'lowestPrice',
		'IamFleetRole': fleet_spec['iam_fleet_role'],
		'TargetCapacity': 1,
		'SpotPrice': '0.972',
		'ValidFrom': '2018-01-19T14:12:43Z',
  		'ValidUntil': '2019-01-19T14:12:43Z',
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
