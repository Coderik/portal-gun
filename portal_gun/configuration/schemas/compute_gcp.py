from marshmallow import fields, Schema, validates_schema, ValidationError

from .provision import ProvisionActionSchema


class GpuSchema(Schema):
	type = fields.String(required=True)
	count = fields.Integer(required=True)

	class Meta:
		ordered = True


class InstanceSchema(Schema):
	name = fields.String()
	type = fields.String(required=True)
	cpu = fields.Integer()
	memory = fields.Integer()		# in Gb
	gpu = fields.Nested(GpuSchema)
	image = fields.String(required=True)
	availability_zone = fields.String(required=True)
	preemptible = fields.Boolean(required=True)

	@validates_schema
	def validate_providers(self, data):
		if data['type'] == 'custom' and ('cpu' not in data or 'memory' not in data):
			raise ValidationError('For "custom" machine type fields "cpu" and "memory" are required')

	class Meta:
		ordered = True


class AuthSchema(Schema):
	private_ssh_key = fields.String(required=True)
	public_ssh_key = fields.String(required=True)
	user = fields.String(required=True)
	group = fields.String(required=True)

	class Meta:
		ordered = True


# class NetworkSchema(Schema):
# 	security_group_id = fields.String(required=True)
# 	subnet_id = fields.String()


class ComputeGcpSchema(Schema):
	provider = fields.String(required=True)
	instance = fields.Nested(InstanceSchema, required=True)
	auth = fields.Nested(AuthSchema, required=True)
	# network = fields.Nested(NetworkSchema, required=True)
	provision_actions = fields.List(fields.Nested(ProvisionActionSchema))

	class Meta:
		ordered = True
