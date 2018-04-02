import threading

from fabric.api import env, hide
from fabric.contrib.project import rsync_project
from fabric.tasks import execute

from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands import common
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config, get_portal_spec
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die


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


def run_periodically(callable, callable_args, delay):
	callable(*callable_args)
	threading.Timer(delay, run_periodically, args=[callable, callable_args, delay]).start()


class OpenChannelCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'channel'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Open channels for files synchronization')
		parser.add_argument('portal', help='Name of portal')

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		# Find, parse and validate configs
		print('Checking configuration...')
		config = get_config(self._args)
		portal_spec, portal_name = get_portal_spec(self._args)

		# Ensure there is at least one channel spec
		with pass_step_or_die('Check specifications for channels',
							  'Portal specification does not contain any channel', print_error=False):
			channels = portal_spec['channels']
			if len(channels) == 0:
				raise Exception()

		print('Done.\n')

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		print('Retrieve associated resources:')

		# Get current user
		with pass_step_or_die('User identity',
							  'Could not get current user identity'):
			user = aws.get_user_identity()

		# Get spot instance
		with pass_step_or_die('Spot instance',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			spot_instance = common.get_spot_instance(aws, portal_name, user['Arn'])

		print('Done.\n')

		host_name = spot_instance['PublicDnsName']

		# Print information about the channels
		print('Channels defined for portal `{}`:'.format(portal_name))
		for i in range(len(channels)):
			channel = channels[i]
			print('\tChannel #{} ({}):'.format(i, channel['direction'].upper()).expandtabs(4))
			print('\t\tLocal:   {}'.format(channel['local_path']).expandtabs(4))
			print('\t\tRemote:  {}'.format(channel['remote_path']).expandtabs(4))
		print('')

		# Specify remote host for ssh
		env.user = portal_spec['spot_instance']['remote_user']
		env.key_filename = [portal_spec['spot_instance']['ssh_key_file']]
		env.hosts = [host_name]

		# Periodically sync files across all channels
		print('Syncing... (press ctrl+C to interrupt)')
		for channel in channels:
			is_upload = channel['direction'] == 'out'
			is_recursive = channel['recursive'] if 'recursive' in channel else False
			delay = 1.0
			if 'delay' in channel:
				delay = channel['delay']
			run_periodically(sync_files, [channel['local_path'], channel['remote_path'], is_upload, is_recursive], delay)
