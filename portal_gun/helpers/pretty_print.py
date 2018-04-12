def print_volume(volume):
	fill_width = 20

	tags = volume['Tags'] if 'Tags' in volume else []

	# Look for Name tag
	name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), '')

	# Transform tags to a different format (also drop Name tag)
	tags = ['{}:{}'.format(tag['Key'], tag['Value']) for tag in tags if tag['Key'] != 'Name']

	try:
		print('{:{fill}} {}'.format('Volume Id:', volume['VolumeId'], fill=fill_width))
		print('{:{fill}} {}'.format('Name:', name, fill=fill_width))
		print('{:{fill}} {}Gb'.format('Size:', volume['Size'], fill=fill_width))
		print('{:{fill}} {}'.format('Availability Zone:', volume['AvailabilityZone'], fill=fill_width))
		print('{:{fill}} {}'.format('State:', volume['State'], fill=fill_width))
		if len(volume['Attachments']) > 0:
			print('{:{fill}} {}'.format('Attached to:', volume['Attachments'][0]['InstanceId'], fill=fill_width))
			print('{:{fill}} {}'.format('Attached as:', volume['Attachments'][0]['Device'], fill=fill_width))
		if len(tags) > 0:
			print('{:{fill}} {}'.format('User Tags:', ' '.join(tags), fill=fill_width))
		print('')
	except KeyError as e:
		exit('Unexpected format of Volume. Key {} is missing'.format(e))
