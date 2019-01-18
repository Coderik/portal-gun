import threading

import portal_gun.fabric as fab
from portal_gun.commands.helpers import get_provider_config, get_portal_spec, get_portal_name, \
	get_provider_from_portal, get_binding_spec
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step
from .base_command import BaseCommand
from .handlers import create_handler


def run_periodically(callable, callable_args, delay):
	callable(*callable_args)
	threading.Timer(delay, run_periodically, args=[callable, callable_args, delay]).start()


class SyncCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'sync'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Synchronize files given a binding')
		parser.add_argument('portal', help='Name of portal')
		parser.add_argument('binding', default=None, help='Name or index of binding', )
		parser.add_argument('-p', '--period', type=float, default=None,
							help='Synchronize periodically (period is set in seconds) until interrupted.')

	def run(self):
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			portal_name = get_portal_name(self._args.portal)
			portal_spec = get_portal_spec(portal_name)
			provider_name = get_provider_from_portal(portal_spec)
			provider_config = get_provider_config(self._args.config, provider_name)

			# If binding is not specified, only show information about available bindings
			if self._args.binding is None:
				self.print_bindings(portal_spec['bindings'], portal_name)
				return

			# Pick correct binding spec
			with step('Check specification for binding',
					  error_message='Could not find binding `{}` in portal specification'.format(self._args.binding)):
				binding = get_binding_spec(portal_spec, self._args.binding)

		# Create appropriate command handler for given cloud provider
		handler = create_handler(provider_name, provider_config)

		identity_file, user, host, disable_known_hosts = handler.get_ssh_params(portal_spec, portal_name)

		# Print information about the binding
		with print_scope('Binding `{}` of portal `{}`:'.format(binding['name'], portal_name), ''):
			self.print_binding(binding)

		# Configure ssh connection via fabric
		fab_conn = fab.create_connection(host, user, identity_file)

		is_upload = binding['direction'] == 'out'
		is_recursive = binding['recursive'] if 'recursive' in binding else False
		allow_delete = binding['allow_delete'] if 'allow_delete' in binding else False

		if self._args.period is None:
			# Sync once
			print('Syncing...')
			fab.sync_files(fab_conn, binding['local_path'], binding['remote_path'],
						   is_upload, is_recursive, allow_delete)
		else:
			# Periodically sync files
			print('Syncing... (press ctrl+C to interrupt)')
			delay = max(self._args.period, 1.0)
			run_periodically(fab.sync_files,
							 [fab_conn, binding['local_path'], binding['remote_path'],
							  is_upload, is_recursive, allow_delete],
							 delay)

	def print_bindings(self, bindings, portal_name):
		with print_scope('Bindings defined for portal `{}`:'.format(portal_name), ''):
			for i in range(len(bindings)):
				binding = bindings[i]
				with print_scope('Binding #{} `{}` ({}):'.format(i, binding['name'], binding['direction'].upper())):
					print('Local:   {}'.format(binding['local_path']))
					print('Remote:  {}'.format(binding['remote_path']))

	def print_binding(self, binding):
		with print_scope('Binding `{}` ({}):'.format(binding['name'], binding['direction'].upper())):
			print('Local:   {}'.format(binding['local_path']))
			print('Remote:  {}'.format(binding['remote_path']))
