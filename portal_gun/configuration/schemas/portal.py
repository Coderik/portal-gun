from marshmallow import fields, Schema
from portal_gun.one_of_schema import OneOfSchema  # replace by the proper marshmallow-oneofschema package

from .compute_aws import ComputeAwsSchema
from .compute_gcp import ComputeGcpSchema


class ComputeSchema(OneOfSchema):
	type_field = 'provider'
	type_field_remove = False
	type_schemas = {
		'aws': ComputeAwsSchema,
		'gcp': ComputeGcpSchema
	}

	def get_obj_type(self, obj):
		# TODO: implement
		return 'aws'


class PersistentVolumeSchema(Schema):
	volume_id = fields.String(required=True)
	device = fields.String(required=True)
	mount_point = fields.String(required=True)

	class Meta:
		ordered = True


class BindingSchema(Schema):
	name = fields.String(required=True)
	direction = fields.String(required=True)
	local_path = fields.String(required=True)
	remote_path = fields.String(required=True)
	recursive = fields.Boolean()
	allow_delete = fields.Boolean()

	class Meta:
		ordered = True


# OBSOLETE
class ChannelSchema(Schema):
	direction = fields.String(required=True)
	local_path = fields.String(required=True)
	remote_path = fields.String(required=True)
	recursive = fields.Boolean()
	delay = fields.Float()

	class Meta:
		ordered = True


class PortalSchema(Schema):
	compute = fields.Nested(ComputeSchema, required=True)
	persistent_volumes = fields.Nested(PersistentVolumeSchema, required=True, many=True)
	bindings = fields.Nested(BindingSchema, many=True)

	class Meta:
		ordered = True
