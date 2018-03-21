from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.commands.aws_client import AwsClient
from portal_gun.context_managers.no_print import NoPrint

import os


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
		with NoPrint():
			config, portal_spec, portal_name = run_preflight_steps(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		# Get current user
		aws_user = aws.get_user_identity()

		# Get spot instance
		instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

		if instance_info is None:
			exit('Portal `{}` does not seem to be opened'.format(portal_name))

		# Get values for ssh
		key_file = portal_spec['spot_instance']['ssh_key_file']
		user = portal_spec['spot_instance']['remote_user']
		host = instance_info['PublicDnsName']

		print('Connecting to the remote machine...')
		print('\tssh -i "{}" {}@{}'.format(key_file, user, host).expandtabs(4))

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
		os.execvp('ssh', ['ssh', '-i', key_file, '{}@{}'.format(user, host)] + preamble)
