from marshmallow import fields, Schema


class ProvisionActionSchema(Schema):
	name = fields.String(required=True)
	args = fields.Dict(required=True)

	class Meta:
		ordered = True
