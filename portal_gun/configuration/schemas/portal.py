from marshmallow import fields, Schema


class SpotInstanceSchema(Schema):
	instance_type = fields.String(required=True)
	image_id = fields.String(required=True)
	key_pair_name = fields.String(required=True)
	identity_file = fields.String(required=True)
	security_group_id = fields.String(required=True)
	availability_zone = fields.String(required=True)
	subnet_id = fields.String(required=True)
	ebs_optimized = fields.Boolean()
	remote_user = fields.String(required=True)
	python_virtual_env = fields.String()
	extra_python_packages = fields.List(fields.String)

	class Meta:
		ordered = True


class SpotFleetSchema(Schema):
	iam_fleet_role = fields.String(required=True)

	class Meta:
		ordered = True


class PersistentVolumeSchema(Schema):
	volume_id = fields.String(required=True)
	device = fields.String(required=True)
	mount_point = fields.String(required=True)

	class Meta:
		ordered = True


class ChannelSchema(Schema):
	direction = fields.String(required=True)
	local_path = fields.String(required=True)
	remote_path = fields.String(required=True)
	recursive = fields.Boolean()
	delay = fields.Float()

	class Meta:
		ordered = True


class PortalSchema(Schema):
	spot_instance = fields.Nested(SpotInstanceSchema, required=True)
	spot_fleet = fields.Nested(SpotFleetSchema, required=True)
	persistent_volumes = fields.Nested(PersistentVolumeSchema, required=True, many=True)
	channels = fields.Nested(ChannelSchema, required=True, many=True)

	class Meta:
		ordered = True
