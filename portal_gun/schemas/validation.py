from portal_gun.schemas.exceptions import MissingFieldError, WrongFieldTypeError
from portal_gun.schemas.config_schema import schema as config_schema


def validate_config(config):
	_validate_recursively(config, config_schema)


def _validate_recursively(config, schema, trace=None):
	# Initialize trace if empty
	if trace is None:
		trace = []

	# Iterate through schema at current level
	for key, item in schema.items():
		# Ensure corresponding item exists in config
		try:
			config_item = config[key]
		except KeyError:
			raise MissingFieldError(trace + [key])

		# If current item represents subsection, validate it recursively
		if type(item) == dict:
			_validate_recursively(config_item, schema[key], trace + [key])
		elif type(item) == type and type(config_item) != item:
			raise WrongFieldTypeError(trace + [key], item)
