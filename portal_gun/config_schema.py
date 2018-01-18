SPOT_INSTANCE_SPEC = {
	'security_group': str,
	'ebs_optimized': bool,
}

SCHEMA = {
	'aws_region': str,
	'aws_access_key': str,
	'aws_secret_key': str,

	'spot_instance_spec': SPOT_INSTANCE_SPEC,
}


def validate(config):
	validate_recursively(config, SCHEMA)


def validate_recursively(config, schema, trace=None):
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
			validate_recursively(config_item, schema[key], trace + [key])
		elif type(item) == type and type(config_item) != item:
			raise WrongFieldTypeError(trace + [key], item)


class ConfigValidationError(Exception):
	def __init__(self, message):
		self.message = message


class MissingFieldError(ConfigValidationError):
	def __init__(self, trace):
		message = 'Required field `{}` is missing'.format('.'.join(trace))
		ConfigValidationError.__init__(self, message)


class WrongFieldTypeError(ConfigValidationError):
	def __init__(self, trace, expected_type):
		message = 'Field `{}` is expected to have type {}'.format('.'.join(trace), expected_type)
		ConfigValidationError.__init__(self, message)
