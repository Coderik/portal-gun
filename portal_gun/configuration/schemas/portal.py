from portal_gun.configuration.fields import *

schema = {
	'spot_instance': rgf({
		'instance_type': rsf(),
		'image_id': rsf(),
		'key_pair_name': rsf(),
		'security_group_id': rsf(),
		'availability_zone': rsf(),
		'subnet_id': rsf(),
		'ebs_optimized': obf(),
		'ssh_key_file': rsf(),
		'remote_user': rsf(),
		'python_virtual_env': rsf(),
		'extra_python_packages': [osf()]
	}),
	'spot_fleet': rgf({
		'iam_fleet_role': rsf()
	}),
	'persistent_volumes': [
		rgf({
			'volume_id': rsf(),
			'device': rsf(),
			'mount_point': rsf()
		})
	],
	'channels': [
		ogf({
			'direction': rsf(),
			'local_path': rsf(),
			'remote_path': rsf(),
			'recursive': obf()
		})
	]
}
