from portal_gun.schemas.portal_schema import schema as portal_schema


def generate_portal_spec():
	return _generate_recursively(portal_schema)


def _generate_recursively(schema):
	if type(schema) == dict:
		# Iterate through current level
		spec = {key: _generate_recursively(item) for key, item in schema.items()}
	elif type(schema) == list:
		if len(schema) != 1:
			raise ValueError('Arrays in schemas should contain exactly one element, but {} was found.'
							 .format(len(schema)))

		# Create wrapping array
		spec = [_generate_recursively(schema[0])]
	else:
		# Create leaf spec
		spec = 'type: {}'.format(schema.__name__)

	return spec




