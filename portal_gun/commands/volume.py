from __future__ import print_function

from portal_gun.commands.helpers import get_provider_config, get_provider_from_env, get_provider_from_user
from portal_gun.context_managers.print_scope import print_scope
from .base_command import BaseCommand
from .handlers import list_providers, describe_providers, create_handler


class VolumeCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

		self._proper_tag_key = 'dimension'
		self._proper_tag_value = 'C-137'
		self._service_tags = [self._proper_tag_key, 'created-by', 'mount-point']
		self._default_size = 50  # Gb
		self._min_size = 1  # Gb
		self._max_size = 16384  # Gb

	@staticmethod
	def cmd():
		return 'volume'

	@classmethod
	def add_subparser(cls, command_parsers):
		parser = command_parsers.add_parser(cls.cmd(), help='Group of subcommands related to persistent volumes')
		provider_group = parser.add_mutually_exclusive_group()
		for desc in describe_providers():
			provider_group.add_argument('--{}'.format(desc['name']), action='store_const', const=desc['name'],
										dest='provider', help='Set {} as cloud provider'.format(desc['long_name']))

		subcommand_parsers = parser.add_subparsers(title='subcommands', dest='subcommand')

		# List
		parser_list = subcommand_parsers.add_parser('list', help='List persistent volumes')
		parser_list.add_argument('-a', '--all', dest='all', action='store_true',
								 help='Show all volumes, not only ones created by Portal Gun.')
		parser_list.set_defaults(actor=lambda handler, args: handler.list_volumes(args))

		# Create
		parser_create = subcommand_parsers.add_parser('create', help='Create new volume')
		parser_create.add_argument('-n', '--name', dest='name', default=None, help='Set name for new volume.')
		parser_create.add_argument('-s', '--size', dest='size', default=None, type=int,
								   help='Set size (in Gb) for new volume.')
		parser_create.add_argument('-z', '--zone', dest='zone', default=None, help='Set availability zone for new volume.')
		parser_create.add_argument('-S', '--snapshot', dest='snapshot', default=None,
								   help='Set Id of a snapshot to create new volume from.')
		parser_create.add_argument('-t', '--tags', nargs='+', dest='tags', metavar='key:value',
								   help='Set user tags for new volume.')
		parser_create.set_defaults(actor=lambda handler, args: handler.create_volume(args))
		# TODO: add silent mode

		# Update
		parser_update = subcommand_parsers.add_parser('update', help='Update persistent volume')
		parser_update.add_argument(dest='volume_id', help='Volume Id.')
		parser_update.add_argument('-n', '--name', dest='name', help='Update name of volume.')
		parser_update.add_argument('-s', '--size', dest='size', type=int, help='Update size of volume.')
		parser_update.add_argument('-t', '--tags', nargs='+', dest='tags', metavar='key:value',
								   help='Add user tags for volume.')
		parser_update.set_defaults(actor=lambda handler, args: handler.update_volume(args))

		# Delete
		parser_delete = subcommand_parsers.add_parser('delete', help='Delete persistent volume')
		parser_delete.add_argument(dest='volume_id', help='Volume Id.')
		parser_delete.add_argument('-f', '--force', dest='force', action='store_true',
								   help='Delete any volume, even not owned.')
		parser_delete.set_defaults(actor=lambda handler, args: handler.delete_volume(args))

	def run(self):
		providers = list_providers()
		provider_name = self._args.provider or \
						get_provider_from_env(choices=providers) or \
						get_provider_from_user(choices=providers)

		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			provider_config = get_provider_config(self._args.config, provider_name)

		# Create appropriate command handler for given cloud provider
		handler = create_handler(provider_name, provider_config)

		# Call corresponding actor to handle selected subcommand
		self._args.actor(handler, self._args)
