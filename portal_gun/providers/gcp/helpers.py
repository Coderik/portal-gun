import re
import math


def get_instance_name(portal_spec, portal_name):
	try:
		name = portal_spec['compute']['instance']['name']
	except KeyError:
		name = portal_name

	# Make name compliant with RFC1035
	name = re.sub(r'[_\s]', '-', name)
	name = re.sub(r'(^[^a-z]*|[^a-z0-9-]|-*$)', '', name.lower())[:63]

	return name


def build_instance_props(portal_spec, instance_name):
	# Define shortcuts
	instance_spec = portal_spec['compute']['instance']
	auth_spec = portal_spec['compute']['auth']
	zone = instance_spec['availability_zone']

	# Construct partial url for machine type
	if instance_spec['type'] == 'custom':
		cpu = instance_spec['cpu']
		if cpu > 1:
			cpu = int(math.ceil(cpu / 2.0) * 2)
		memory = int(math.ceil(instance_spec['memory'] * 4.0)) * 256
		machine_type = 'zones/{}/machineTypes/custom-{}-{}'.format(zone, cpu, memory)
	else:
		machine_type = 'zones/{}/machineTypes/{}'.format(zone, instance_spec['type'])

	# Read public key from file
	with open(auth_spec['public_ssh_key'], 'r') as f:
		public_ssh_key = f.readline()

	# Fill props
	props = {
		'scheduling': {
			'preemptible': instance_spec['preemptible']
		},
		'networkInterfaces': [
			{
				'network': 'global/networks/default',
				'accessConfigs': [
					{
						'name': 'External NAT',
						'type': 'ONE_TO_ONE_NAT'
					}
				]
			}
		],
		'machineType': machine_type,
		'name': instance_name,
		'disks': [{
			'initializeParams': {
				'diskName': '{}-boot'.format(instance_name),
				'diskSizeGb': 20,
				'sourceImage': 'global/images/{}'.format(instance_spec['image'])

			},
			'autoDelete': True,
			'boot': True
		}],
		'metadata': {
			'items': [
				{
					'key': 'ssh-keys',
					'value': '{}:{}'.format(auth_spec['user'], public_ssh_key)
				}
			]
		}
	}

	# Specify GPU, if needed
	if 'gpu' in instance_spec:
		props['guestAccelerators'] = [{
			'acceleratorType': 'zones/{}/acceleratorTypes/{}'.format(zone, instance_spec['gpu']['type']),
			'acceleratorCount': instance_spec['gpu']['count']
		}]

	# Add persistent volumes
	for volume in portal_spec['persistent_volumes']:
		props['disks'].append({
			'source': 'zones/{}/disks/{}'.format(zone, volume['volume_id']),
			'mode': 'READ_WRITE',
			'autoDelete': False,
			'boot': False
		})

	return props
