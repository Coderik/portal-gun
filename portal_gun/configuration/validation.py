from portal_gun.configuration.schemas.config import schema as config_schema
from portal_gun.configuration.schemas.portal import schema as portal_schema
from portal_gun.configuration.fields.group_field import BaseField
from portal_gun.configuration.fields.value_field import ValueField
from portal_gun.configuration.fields.group_field import GroupField
from portal_gun.configuration.exceptions import MissingFieldError, WrongFieldTypeError, SchemaError


def validate_config(config):
	return _validate(config, config_schema)


def validate_portal_spec(portal_spec):
	return _validate(portal_spec, portal_schema)


def _validate(config, schema):
	try:
		_validate_recursively(config, schema, [])
	except (MissingFieldError, WrongFieldTypeError) as e:
		return e.message

	return None


def _validate_recursively(config, schema, trace):
	config_type = type(config)
	schema_type = type(schema)

	# If field is missing from config, ensure that it is optional
	if config is None:
		if issubclass(schema_type, BaseField):
			if schema.is_required():
				raise MissingFieldError(trace)
		elif schema_type == list:
			if len(schema) != 1:
				raise SchemaError('Arrays in schemas should contain exactly one element, but {} was found.'
								  .format(len(schema)))
			_validate_recursively(None, schema[0], trace)
		else:
			raise SchemaError('Unexpected field type `{}` in schema.'.format(schema_type.__name__))

		return  # filed is optional

	if schema_type == dict or schema_type == GroupField:
		# Ensure config field has expected type
		if config_type != dict:
			raise WrongFieldTypeError(trace, dict)

		# Iterate through nested fields of schema
		for key, schema_field in schema.items():
			# Try to get corresponding item from config
			try:
				config_field = config[key]
			except KeyError:
				config_field = None

			_validate_recursively(config_field, schema_field, trace + [key])
	elif schema_type == list:
		# Ensure array field of schema contains exactly one element
		if len(schema) != 1:
			raise SchemaError('Arrays in schemas should contain exactly one element, but {} was found.'
							  .format(len(schema)))

		# Ensure config field has expected type
		if config_type != list:
			raise WrongFieldTypeError(trace, list)

		schema_field = schema[0]

		# If array in config is empty, ensure that it is optional
		if len(config) == 0:
			_validate_recursively(None, schema_field, trace)

		# Validate every item of array in config
		for config_field in config:
			_validate_recursively(config_field, schema_field, trace)
	elif schema_type == ValueField:
		if config_type != schema.field_type():
			raise WrongFieldTypeError(trace, schema.field_type())
	else:
		raise SchemaError('Unexpected field type `{}` in schema.'.format(schema_type.__name__))
