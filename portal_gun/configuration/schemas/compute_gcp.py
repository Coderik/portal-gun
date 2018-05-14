from marshmallow import fields, Schema

from .provision import ProvisionActionSchema


class InstanceSchema(Schema):
	name = fields.String()
	type = fields.String(required=True)
	image = fields.String(required=True)
	availability_zone = fields.String(required=True)
	preemptible = fields.Boolean(required=True)


class AuthSchema(Schema):
	private_ssh_key = fields.String(required=True)
	public_ssh_key = fields.String(required=True)
	user = fields.String(required=True)
	group = fields.String(required=True)


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
