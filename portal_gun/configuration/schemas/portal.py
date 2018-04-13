from marshmallow import fields, Schema


class SpotInstanceSchema(Schema):
	instance_type = fields.String(required=True, default='string')
	image_id = fields.String(required=True, default='string')
	key_pair_name = fields.String(required=True, default='string')
	security_group_id = fields.String(required=True, default='string')
	availability_zone = fields.String(required=True, default='string')
	subnet_id = fields.String(required=True, default='string')
	ebs_optimized = fields.Boolean()
	ssh_key_file = fields.String(required=True, default='string')
	remote_user = fields.String(required=True, default='string')
	python_virtual_env = fields.String(required=True, default='string')
	extra_python_packages = fields.List(fields.String)

	class Meta:
		ordered = True


class SpotFleetSchema(Schema):
	iam_fleet_role = fields.String(required=True, default='string')

	class Meta:
		ordered = True


class PersistentVolumeSchema(Schema):
	volume_id = fields.String(required=True, default='string')
	device = fields.String(required=True, default='string')
	mount_point = fields.String(required=True, default='string')

	class Meta:
		ordered = True


class ChannelSchema(Schema):
	direction = fields.String(required=True, default='string')
	local_path = fields.String(required=True, default='string')
	remote_path = fields.String(required=True, default='string')
	recursive = fields.Boolean()
	delay = fields.Float()

	class Meta:
		ordered = True


class PortalSchema(Schema):
	spot_instance = fields.Nested(SpotInstanceSchema, required=True, default=SpotInstanceSchema().dump(None))
	spot_fleet = fields.Nested(SpotFleetSchema, required=True, default=SpotFleetSchema().dump(None))
	persistent_volumes = fields.Nested(PersistentVolumeSchema, required=True, many=True,
									   default=[PersistentVolumeSchema().dump(None)])
	channels = fields.Nested(ChannelSchema, many=True, default=[ChannelSchema().dump(None)])

	class Meta:
		ordered = True
