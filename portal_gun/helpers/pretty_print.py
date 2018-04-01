def print_volume(volume):
	fill_width = 20
	print('{:{fill}} {}'.format('Volume Id:', volume['VolumeId'], fill=fill_width))
	print('{:{fill}} {}Gb'.format('Size:', volume['Size'], fill=fill_width))
	print('{:{fill}} {}'.format('Availability Zone:', volume['AvailabilityZone'], fill=fill_width))
	print('{:{fill}} {}'.format('State:', volume['State'], fill=fill_width))
	if len(volume['Attachments']) > 0:
		print('{:{fill}} {}'.format('Attached to:', volume['Attachments'][0]['InstanceId'], fill=fill_width))
		print('{:{fill}} {}'.format('Attached as:', volume['Attachments'][0]['Device'], fill=fill_width))
	print('')
