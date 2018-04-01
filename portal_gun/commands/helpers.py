from os import path
import json

from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.configuration.validation import validate_portal_spec, validate_config
from portal_gun.configuration.exceptions import ConfigValidationError


def get_config(args):
	# Parse global config
	with pass_step_or_die('Parse config file', 'Could not parse config file', errors=[IOError, ValueError]):
		with open(args.config) as config_file:
			config = json.load(config_file)

	# Validate global config
	with pass_step_or_die('Validate config', 'Config is not valid', errors=[ConfigValidationError]):
		validate_config(config)

	return config


def get_portal_spec(args):
	# Get portal name and spec file
	portal_name = args.portal.rsplit('.', 1)[0]
	spec_filename = '{}.json'.format(portal_name)

	# Ensure spec file exists
	with pass_step_or_die('Locate portal specification file',
						  'Could not find portal specification file `{}`.'.format(spec_filename)):
		if not path.exists(spec_filename):
			raise Exception()

	# Parse portal spec file
	with pass_step_or_die('Parse portal specification file', 'Could not parse portal specification file',
						  errors=[IOError, ValueError]):
		with open(spec_filename) as spec_file:
			portal_spec = json.load(spec_file)

	# Validate portal spec
	with pass_step_or_die('Validate portal specification', 'Portal specification is not valid',
						  errors=[ConfigValidationError]):
		validate_portal_spec(portal_spec)

	return portal_spec, portal_name
