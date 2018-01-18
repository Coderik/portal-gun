schema = {
	'spot_instance_spec': {
		'instance_type': str,
		'image_id': str,
		'key_pair_name': str,
		'security_group': str,
		'ebs_optimized': bool,
		'spot_price': str
	},
	'persistent_volume_spec': [
		{
			'volume_id': str,
			'instance_id': str,
			'device': str
		}
	]
}
