import json
from os import path
from collections import OrderedDict

from marshmallow import fields
from portal_gun.one_of_schema import OneOfSchema  # replace by the proper marshmallow-oneofschema package

from portal_gun.configuration.schemas import ConfigSchema, PortalSchema, ValidationError
from portal_gun.configuration.constants import config_paths
from portal_gun.context_managers.step import step


def get_provider_config(args, provider_name):
	# Parse general config
	with step('Parse general config file', catch=[IOError, ValueError]):
		config_path = args.config

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


def get_portal_name(args):
	return args.portal.rsplit('.', 1)[0]


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


def get_provider_from_portal(portal_spec):
	return portal_spec['compute']['provider']


def generate_draft(schema, selectors=None):
	"""
	Generate draft config from a given schema.
	:param schema:
	:param selectors: Dictionary that maps types of polymorphic schemas to names of particular schemas ({type: string})
	:return:
	"""
	return _process_schema(schema, selectors)


def _process_schema(schema, selectors=None):
	draft = OrderedDict()

	if isinstance(schema, OneOfSchema):
		# If given schema is polymorphic (has type OneOfSchema),
		# use given selectors to replace it by a particular schema
		try:
			type_field = schema.type_field
			schema_name = selectors[type(schema)]
			schema = schema.type_schemas[schema_name]()
			draft[type_field] = schema_name
		except KeyError:
			return draft

	for field_name, field in schema.fields.items():
		draft[field_name] = _process_field(field, selectors)

	return draft


def _process_field(field, selectors=None):
	if isinstance(field, fields.Nested):
		field_value = _process_schema(field.schema, selectors)
		if field.schema.many:
			field_value = [field_value]
	elif isinstance(field, fields.List):
		field_value = [_process_field(field.container, selectors)]
	else:
		field_value = _describe_field(field)

	return field_value


def _describe_field(field):
	description = field.__class__.__name__.lower()
	requirement = 'required' if field.required else 'optional'
	return '{} ({})'.format(description, requirement)
