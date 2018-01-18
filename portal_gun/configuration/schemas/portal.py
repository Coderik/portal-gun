from portal_gun.configuration.fields import *

schema = {
	'spot_instance_spec': rgf({
		'instance_type': rsf(),
		'image_id': rsf(),
		'key_pair_name': rsf(),
		'security_group': rsf(),
		'ebs_optimized': obf(),
		'spot_price': osf()
	}),
	'persistent_volume_spec': [
		rgf({
			'volume_id': rsf(),
			'instance_id': rsf(),
			'device': rsf()
		})
	]
}
