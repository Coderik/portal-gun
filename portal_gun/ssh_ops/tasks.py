from fabric.api import sudo, run
from fabric.context_managers import prefix


def mount_volume(device, mounting_point, user, group):
	# Inspect volume's file system
	out = sudo('file -s {}'.format(device))

	# Ensure volume contains a file system
	has_file_system = out != '{}: data'.format(device)
	if not has_file_system:
		sudo('mkfs -t ext4 {}'.format(device))

	# Create mounting point
	run('mkdir -p {}'.format(mounting_point))

	# Mount volume
	sudo('mount {} {}'.format(device, mounting_point))

	# If file system has just been created, fix group and user of the mounting point
	if not has_file_system:
		sudo('chown -R {}:{} {}'.format(group, user, mounting_point))


def install_python_packages(virtual_env, packages):
	with prefix('source activate {}'.format(virtual_env)):
		run('pip install {}'.format(' '.join(packages)))
