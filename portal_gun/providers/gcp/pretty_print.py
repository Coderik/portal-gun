def print_volume(volume):
	fill_width = 20

	users = volume['users'] if 'users' in volume else []
	tags = volume['labels'] if 'labels' in volume else {}
	tags = ['{}:{}'.format(key, value) for key, value in tags.items()]

	state = 'in-use' if len(users) > 0 else 'available'

	try:
		print('{:{fill}} {}'.format('Volume Id:', volume['id'], fill=fill_width))
		print('{:{fill}} {}'.format('Name:', volume['name'], fill=fill_width))
		print('{:{fill}} {}Gb'.format('Size:', volume['sizeGb'], fill=fill_width))
		print('{:{fill}} {}'.format('Availability Zone:', volume['zone'], fill=fill_width))
		print('{:{fill}} {}'.format('State:', state, fill=fill_width))
		for user in users:
			print('{:{fill}} {}'.format('Attached to:', user.rsplit('/', 1)[1], fill=fill_width))
			# print('{:{fill}} {}'.format('Attached as:', volume['Attachments'][0]['Device'], fill=fill_width))
		if len(tags) > 0:
			print('{:{fill}} {}'.format('User Tags:', ' '.join(tags), fill=fill_width))
		print('')
	except KeyError as e:
		exit('Unexpected format of Volume. Key {} is missing'.format(e))
