import os

from portal_gun.configuration.helpers import get_provider_config, get_portal_spec, get_portal_name, \
	get_provider_from_portal
from portal_gun.context_managers.no_print import no_print
from .base_command import BaseCommand
from .handlers import create_handler


class SshCommand(BaseCommand):
	DEFAULT_TMUX_SESSION = 'portal'

	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'ssh'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Connect to the remote host via ssh')
		parser.add_argument('portal', help='Name of portal')
		parser.add_argument('-t', '--tmux', dest='tmux', nargs='?', default=None, const=cls.DEFAULT_TMUX_SESSION,
							metavar='session', help='Automatically open tmux session upon connection. '
													'Default session name is `{}`.'.format(cls.DEFAULT_TMUX_SESSION))

	def run(self):
		# Find, parse and validate configs
		with no_print():
			portal_name = get_portal_name(self._args)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args, provider_name)

			# Create appropriate command handler for given cloud provider
			handler = create_handler(provider_name, provider_config)

			identity_file, user, host = handler.get_ssh_params(portal_spec, portal_name)

		print('Connecting to the remote machine...')
		print('\tssh -i "{}" {}@{}'.format(identity_file, user, host).expandtabs(4))

		# If requested, configure a preamble (a set of commands to be run automatically after connection)
		preamble = []
		if self._args.tmux is not None:
			preamble = [
				'-t',
				'""tmux attach-session -t {sess} || tmux new-session -s {sess}""'.format(sess=self._args.tmux)
			]
			print('Upon connection will open tmux session `{}`.'.format(self._args.tmux))

		print('')

		# Ssh to remote host (effectively replace current process by ssh)
		os.execvp('ssh', ['ssh', '-i', identity_file, '{}@{}'.format(user, host)] + preamble)
