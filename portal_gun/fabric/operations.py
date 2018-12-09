from invoke.vendor import six
import fabric.connection


def create_connection(host, user, identity_file):
	return fabric.connection.Connection(host=host,
										 user=user,
										 connect_kwargs={
											 'key_filename': identity_file,
										 })


def mount_volume(conn, device, mounting_point, user, group):
	# Catch tail of greeting output
	res = conn.sudo('whoami')

	# Inspect volume's file system
	res = conn.sudo('file -s {}'.format(device))

	# Ensure volume contains a file system
	has_file_system = res.stdout != '{}: data'.format(device)
	if not has_file_system:
		conn.sudo('mkfs -t ext4 {}'.format(device))

	# Create mounting point
	res = conn.run('mkdir -p {}'.format(mounting_point))

	# Mount volume
	res = conn.sudo('mount {} {}'.format(device, mounting_point))

	# If file system has just been created, fix group and user of the mounting point
	if not has_file_system:
		res = conn.sudo('chown -R {}:{} {}'.format(group, user, mounting_point))


def install_python_packages(conn, virtual_env, packages):
	if not packages:
		return

	with conn.prefix('source activate {}'.format(virtual_env)):
		conn.run('pip install {}'.format(' '.join(packages)))


def install_packages(conn, packages):
	if not packages:
		return

	# TODO: handle locked /var/lib/dpkg/lock
	conn.sudo('apt install -y {}'.format(' '.join(packages)))


def sync_files(conn, local_path, remote_path, is_upload, is_recursive, allow_delete=False, strict_host_keys=True):
	"""This code was ported from https://github.com/fabric/patchwork and extended for two-way transfer. """
	exclude = ()
	ssh_opts = ""

	rsync_opts = '--out-format="[%t] {} %f %\'\'b"'.format('OUT' if is_upload else 'IN')
	if is_recursive:
		rsync_opts += ' -r'

	# Turn single-string exclude into a one-item list for consistency
	if isinstance(exclude, six.string_types):
		exclude = [exclude]
	# Create --exclude options from exclude list
	exclude_opts = ' --exclude "{}"' * len(exclude)
	# Double-backslash-escape
	exclusions = tuple([str(s).replace('"', '\\\\"') for s in exclude])
	# Honor SSH key(s)
	key_string = ""
	# TODO: seems plausible we need to look in multiple places if there's too
	# much deferred evaluation going on in how we eg source SSH config files
	# and so forth, re: connect_kwargs
	# TODO: we could get VERY fancy here by eg generating a tempfile from any
	# in-memory-only keys...but that's also arguably a security risk, so...
	keys = conn.connect_kwargs.get("key_filename", [])
	# TODO: would definitely be nice for Connection/FabricConfig to expose an
	# always-a-list, always-up-to-date-from-all-sources attribute to save us
	# from having to do this sort of thing. (may want to wait for Paramiko auth
	# overhaul tho!)
	if isinstance(keys, six.string_types):
		keys = [keys]
	if keys:
		key_string = "-i " + " -i ".join(keys)
	# Get base cxn params
	user, host, port = conn.user, conn.host, conn.port
	port_string = "-p {}".format(port)
	# Remote shell (SSH) options
	rsh_string = ""
	# Strict host key checking
	disable_keys = "-o StrictHostKeyChecking=no"
	if not strict_host_keys and disable_keys not in ssh_opts:
		ssh_opts += " {}".format(disable_keys)
	rsh_parts = [key_string, port_string, ssh_opts]
	if any(rsh_parts):
		rsh_string = "--rsh='ssh {}'".format(" ".join(rsh_parts))
	# Set up options part of string
	options_map = {
		"delete": "--delete" if allow_delete else "",
		"exclude": exclude_opts.format(*exclusions),
		"rsh": rsh_string,
		"extra": rsync_opts,
	}
	options = "{delete}{exclude} -pthrvz {extra} {rsh}".format(**options_map)

	# Create and run final command string
	# TODO: richer host object exposing stuff like .address_is_ipv6 or whatever
	if host.count(":") > 1:
		# Square brackets are mandatory for IPv6 rsync address,
		# even if port number is not specified
		cmd = "rsync {opt:} {local:} [{user:}@{host:}]:{remote:}" if is_upload else "rsync {opt:} [{user:}@{host:}]:{remote:} {local:}"
	else:
		cmd = "rsync {opt:} {local:} {user:}@{host:}:{remote:}" if is_upload else "rsync {opt:} {user:}@{host:}:{remote:} {local:}"

	cmd = cmd.format(opt=options, local=local_path, user=user, host=host, remote=remote_path)
	res = conn.local(cmd, hide=True)

	# Get transferred files
	transferred_files = res.stdout.strip('\n').split('\n')[1:-3]

	if len(transferred_files) > 0:
		print('\n'.join(transferred_files))


__all__ = [
	'create_connection',
	'mount_volume',
	'install_python_packages',
	'install_packages',
	'sync_files'
]
