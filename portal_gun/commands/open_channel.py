import boto3
from fabric.tasks import execute
from fabric.api import env, hide
from fabric.contrib.project import rsync_project

from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands import common


def sync_files(local_path, remote_path, is_upload, is_recursive):
	return rsync_project(remote_path, local_path, delete=True, upload=is_upload, capture=True)


class OpenChannelCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'channel'

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))
		print('Make preflight checks:')

		config, portal_spec, portal_name = run_preflight_steps(self._args)

		# Ensure there is at least one channel spec
		with pass_step_or_die('Check specifications for channels',
							  'Portal specification does not contain any channel', print_error=False):
			channels = portal_spec['channels']
			if len(channels) == 0:
				raise Exception()

		print('Preflight checks are complete.\n')

		# Create EC2 client
		ec2_client = boto3.client('ec2',
								  config['aws_region'],
								  aws_access_key_id=config['aws_access_key'],
								  aws_secret_access_key=config['aws_secret_key'])

		print('Retrieve associated resources:')

		# Get current user
		with pass_step_or_die('User identity',
							  'Could not get current user identity'.format(portal_name)):
			user = common.get_user_identity(config['aws_access_key'], config['aws_secret_key'])

		# Get spot instance
		with pass_step_or_die('Spot instance',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			spot_instance = common.get_spot_instance(ec2_client, portal_name, user['Arn'])

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

		# TODO: run periodically
		for channel in channels:
			is_upload = channel['direction'] == 'out'
			is_recursive = channel['recursive'] if 'recursive' in channel else False
			with hide('running', 'stdout'):
				output = execute(sync_files, channel['local_path'], channel['remote_path'], is_upload, is_recursive)

			# TODO: parse output to print only moved files
			print('>>>{}<<<'.format(output))
