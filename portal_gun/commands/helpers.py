

import json
from os import path, environ

from portal_gun.configuration.constants import config_paths, cloud_provider_env
from portal_gun.configuration.schemas import ConfigSchema, PortalSchema, ValidationError
from portal_gun.context_managers.step import step


def get_provider_config(config_path, provider_name):
	# Parse general config
	with step('Parse general config file', catch=[IOError, ValueError]):
		# If config file is not specified in arguments, look for it in default locations
		if config_path is None:
			for p in config_paths:
				if path.exists(p):
					config_path = p
					break
			else:
				raise ValueError('Could not find config file')

		with open(config_path) as config_file:
			config_data = json.load(config_file)

	# Validate global config
	with step('Validate general config', catch=[ValidationError]):
		config = ConfigSchema().load(config_data)

	# Retrieve cloud provider config
	with step('Retrieve provider config ({})'.format(provider_name),
			  error_message='Cloud provider {} is not configured'.format(provider_name), catch=[KeyError]):
		provider_config = config[provider_name]

	return provider_config


def get_portal_name(portal_arg):
	return portal_arg.rsplit('.', 1)[0]


def get_portal_spec(portal_name):
	# Get portal spec file
	spec_filename = '{}.json'.format(portal_name)

	# Ensure spec file exists
	with step('Locate portal specification file'):
		if not path.exists(spec_filename):
			raise Exception('Could not find portal specification file `{}`.'.format(spec_filename))

	# Parse portal spec file
	with step('Parse portal specification file', catch=[IOError, ValueError]):
		with open(spec_filename) as spec_file:
			portal_spec_data = json.load(spec_file)

	# Validate portal spec
	with step('Validate portal specification', catch=[ValidationError]):
		portal_spec = PortalSchema().load(portal_spec_data)

	return portal_spec


def get_binding_spec(portal_spec, binding_id):
	bindings = portal_spec['bindings']

	for binding in bindings:
		if str(binding_id) in binding['name']:
			return binding

	index = int(binding_id)
	return bindings[index]


def get_provider_from_portal(portal_spec):
	return portal_spec['compute']['provider']


def get_provider_from_env(choices):
	try:
		provider = environ[cloud_provider_env]
		if provider in choices:
			return provider
	except KeyError:
		pass

	return None


def get_provider_from_user(choices):
	provider = None
	while provider is None:
		print('Select cloud provider [{}]: '.format(', '.join(choices)), end='')
		provider = input() or None
		if provider not in choices:
			provider = None

	print()

	return provider


__all__ = [
	'get_provider_config',
	'get_portal_name',
	'get_portal_spec',
	'get_binding_spec',
	'get_provider_from_portal',
	'get_provider_from_env',
	'get_provider_from_user'
]
