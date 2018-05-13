from marshmallow import fields, Schema, validates_schema, ValidationError


class AwsSchema(Schema):
	region = fields.String(required=True, default='string')
	access_key = fields.String(required=True, default='string')
	secret_key = fields.String(required=True, default='string')

	class Meta:
		ordered = True


class GcpSchema(Schema):
	project = fields.String(required=True, default='string')
	region = fields.String(required=True, default='string')
	service_account_file = fields.String(required=True, default='string')

	class Meta:
		ordered = True


class ConfigSchema(Schema):
	aws = fields.Nested(AwsSchema)
	gcp = fields.Nested(GcpSchema)

	@validates_schema
	def validate_providers(self, data):
		if len(data) == 0:
			raise ValidationError('Configuration for at least one cloud provider should be specified')
