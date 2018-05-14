from fabric.api import env, hide
from fabric.tasks import execute
from fabric.contrib.project import rsync_project

from portal_gun.ssh_ops import tasks


def configure(identity_file, user, host, disable_known_hosts=False):
	env.key_filename = [identity_file]
	env.user = user
	env.hosts = [host]
	env.disable_known_hosts = disable_known_hosts
	env.connection_attempts = 5


def mount_volume(device, mount_point, user, group):
	with hide('running', 'stdout'):
		execute(tasks.mount_volume, device, mount_point, user, group)


def install_python_packages(virtual_env, packages):
	if not packages:
		return

	with hide('running', 'stdout'):
		execute(tasks.install_python_packages, virtual_env, packages)


def sync_files(local_path, remote_path, is_upload, is_recursive):
	extra_opts = '--out-format="[%t] {} %f %\'\'b"'.format('OUT' if is_upload else 'IN')
	if is_recursive:
		extra_opts += ' -r'

	with hide('running', 'stdout'):
		output = execute(rsync_project, remote_path, local_path, delete=True, upload=is_upload, capture=True,
						 extra_opts=extra_opts)

	# Get raw stdout output
	output = output.values()[0]

	# Get transferred files
	transferred_files = output.split('\n')[1:-3]

	if len(transferred_files) > 0:
		print('\n'.join(transferred_files))


__all__ = [
	'configure',
	'mount_volume',
	'install_python_packages',
	'sync_files'
]
