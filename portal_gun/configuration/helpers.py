import json
from os import path
from collections import OrderedDict

from marshmallow import fields

from portal_gun.configuration.schemas import ConfigSchema, PortalSchema, ValidationError
from portal_gun.configuration.constants import config_paths
from portal_gun.context_managers.step import step


def get_config(args):
	# Parse global config
	with step('Parse config file', catch=[IOError, ValueError]):
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
	with step('Validate config', catch=[ValidationError]):
		config = ConfigSchema().load(config_data)

	return config


def get_portal_spec(args):
	# Get portal name and spec file
	portal_name = args.portal.rsplit('.', 1)[0]
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

	return portal_spec, portal_name


def generate_draft(schema):
	"""
	Generate draft config from a given schema.
	:param schema:
	:return:
	"""
	draft = OrderedDict()

	for field_name, field in schema.fields.items():
		if field.__class__ is fields.Nested:
			field_value = generate_draft(field.schema)
			if field.schema.many:
				field_value = [field_value]
		elif field.__class__ is fields.List:
			field_value = [_describe_field(field.container)]
		else:
			field_value = _describe_field(field)

		draft[field_name] = field_value

	return draft


def _describe_field(field):
	description = field.__class__.__name__.lower()
	requirement = 'required' if field.required else 'optional'
	return '{} ({})'.format(description, requirement)
