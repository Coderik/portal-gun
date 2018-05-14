import threading

import portal_gun.ssh_ops as ssh
from portal_gun.commands.helpers import get_provider_config, get_portal_spec, get_portal_name, \
	get_provider_from_portal
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step
from .base_command import BaseCommand
from .handlers import create_handler


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
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			portal_name = get_portal_name(self._args.portal)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args.config, provider_name)

			# Ensure there is at least one channel spec
			with step('Check specifications for channels',
					  error_message='Portal specification does not contain any channel'):
				channels = portal_spec['channels']
				if len(channels) == 0:
					raise Exception()

		# Create appropriate command handler for given cloud provider
		handler = create_handler(provider_name, provider_config)

		identity_file, user, host, disable_known_hosts = handler.get_ssh_params(portal_spec, portal_name)

		# Print information about the channels
		with print_scope('Channels defined for portal `{}`:'.format(portal_name), ''):
			for i in range(len(channels)):
				channel = channels[i]
				with print_scope('Channel #{} ({}):'.format(i, channel['direction'].upper())):
					print('Local:   {}'.format(channel['local_path']))
					print('Remote:  {}'.format(channel['remote_path']))

		# Configure ssh connection via fabric
		ssh.configure(identity_file, user, host, disable_known_hosts)

		# Periodically sync files across all channels
		print('Syncing... (press ctrl+C to interrupt)')
		for channel in channels:
			is_upload = channel['direction'] == 'out'
			is_recursive = channel['recursive'] if 'recursive' in channel else False
			delay = 1.0
			if 'delay' in channel:
				delay = channel['delay']
			run_periodically(ssh.sync_files,
							 [channel['local_path'], channel['remote_path'], is_upload, is_recursive], delay)
