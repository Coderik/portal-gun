from marshmallow import fields, Schema


class ConfigSchema(Schema):
	aws_region = fields.String(required=True, default='string')
	aws_access_key = fields.String(required=True, default='string')
	aws_secret_key = fields.String(required=True, default='string')

	class Meta:
		ordered = True
