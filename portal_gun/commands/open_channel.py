from fabric.tasks import execute
from fabric.api import env, hide
from fabric.contrib.project import rsync_project

from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die


def sync_files(local_path, remote_path, is_upload, is_recursive):
	return rsync_project(remote_path, local_path, delete=True, upload=is_upload, capture=True)


class OpenChannelCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))
		print('\tPreflight checks:'.expandtabs(4))

		config, portal_spec, portal_name = run_preflight_steps(self._args)

		# Ensure there is at least one channel spec
		with pass_step_or_die('Check specifications for channels',
							  'Portal specification does not contain any channel', print_error=False):
			channels = portal_spec['channels']
			if len(channels) == 0:
				raise Exception()

		print('\tPreflight checks are complete.\n'.expandtabs(4))

		# Print information about the channels
		print('\tChannels defined for portal `{}`:'.format(portal_name).expandtabs(4))
		for i in range(len(channels)):
			channel = channels[i]
			print('\t\tChannel #{} ({}):'.format(i, channel['direction'].upper()).expandtabs(4))
			print('\t\t\tLocal:   {}'.format(channel['local_path']).expandtabs(4))
			print('\t\t\tRemote:  {}'.format(channel['remote_path']).expandtabs(4))
		# print('\t\t\tDirection:  {}'.format(channel['direction']).expandtabs(4))
		print('')

		# TODO:
		# - find instance by tag and ensure it is running
		# - get its host name
		host_name = "ec2-34-242-109-27.eu-west-1.compute.amazonaws.com"

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



	@staticmethod
	def cmd():
		return 'channel'
