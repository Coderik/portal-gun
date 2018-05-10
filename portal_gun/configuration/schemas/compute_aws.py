from marshmallow import fields, Schema

from .provision import ProvisionActionSchema


class InstanceSchema(Schema):
	type = fields.String(required=True)
	image_id = fields.String(required=True)
	availability_zone = fields.String(required=True)
	ebs_optimized = fields.Boolean()
	iam_fleet_role = fields.String(required=True)

	class Meta:
		ordered = True


class AuthSchema(Schema):
	key_pair_name = fields.String(required=True)
	identity_file = fields.String(required=True)
	user = fields.String(required=True)
	group = fields.String(required=True)

	class Meta:
		ordered = True


class NetworkSchema(Schema):
	security_group_id = fields.String(required=True)
	subnet_id = fields.String()

	class Meta:
		ordered = True


class ComputeAwsSchema(Schema):
	instance = fields.Nested(InstanceSchema, required=True)
	auth = fields.Nested(AuthSchema, required=True)
	network = fields.Nested(NetworkSchema, required=True)
	provision_actions = fields.Nested(ProvisionActionSchema, many=True)

	class Meta:
		ordered = True
