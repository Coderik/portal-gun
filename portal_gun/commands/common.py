def get_spot_instance(aws_client, portal_name, user):
	spot_instance = aws_client.find_spot_instance(portal_name, user)

	if spot_instance is None:
		raise RuntimeError('Instance is not running')

	return spot_instance


def get_spot_fleet_request(aws_client, spot_fleet_request_id):
	spot_fleet_request = aws_client.get_spot_fleet_request(spot_fleet_request_id)

	if spot_fleet_request is None:
		raise RuntimeError('Could not find spot instance request')

	return spot_fleet_request


def check_instance_not_exists(aws_client, portal_name, user):
	spot_instance = aws_client.find_spot_instance(portal_name, user)

	if spot_instance is not None:
		raise RuntimeError('Instance is already running')


def check_volumes_availability(aws_client, volume_ids):
	volumes = aws_client.get_volumes(volume_ids)

	if not all([volume['State'] == 'available' for volume in volumes]):
		states = ['{} is {}'.format(volume['VolumeId'], volume['State']) for volume in volumes]
		raise RuntimeError(', '.join(states))
