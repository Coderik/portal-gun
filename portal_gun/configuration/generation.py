from portal_gun.configuration.exceptions import SchemaError
from portal_gun.configuration.schemas.portal import schema as portal_schema
from portal_gun.configuration.fields.value_field import ValueField
from portal_gun.configuration.fields.group_field import GroupField


def generate_portal_spec():
	return _generate_recursively(portal_schema)


def _generate_recursively(field):
	"""
	Recursively generate draft of a specification for a given field of a schema.
	:param field: Root, intermediate or leaf field of the given schema.
	:return: dict containing specification draft
	"""

	field_type = type(field)
	if field_type == dict or field_type == GroupField:
		# Iterate through root or group field
		spec = {key: _generate_recursively(item) for key, item in field.items()}
	elif field_type == list:
		if len(field) != 1:
			raise SchemaError('Arrays in schemas should contain exactly one element, but {} was found.'
							 .format(len(field)))

		# Create wrapping array
		spec = [_generate_recursively(field[0])]
	elif field_type == ValueField:
		# Describe leaf-level Value Field
		spec = str(field)
	else:
		raise SchemaError('Unexpected field type `{}` in schema.'.format(field_type.__name__))

	return spec
