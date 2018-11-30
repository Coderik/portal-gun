from collections import OrderedDict

from marshmallow import fields

from portal_gun.one_of_schema import OneOfSchema  # replace by the proper marshmallow-oneofschema package


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
