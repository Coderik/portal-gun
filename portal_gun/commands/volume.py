from __future__ import print_function

from portal_gun.aws.aws_client import AwsClient
from portal_gun.aws.helpers import from_aws_tags
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config
from portal_gun.commands.exceptions import CommandError
from portal_gun.helpers.pretty_print import print_volume
from portal_gun.context_managers.step import step
from portal_gun.context_managers.print_scope import print_scope


class VolumeCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

		self._proper_tag_key = 'dimension'
		self._proper_tag_value = 'C-137'
		self._service_tags = [self._proper_tag_key, 'created-by']
		self._default_size = 50  # Gb
		self._min_size = 1  # Gb
		self._max_size = 16384  # Gb

	@staticmethod
	def cmd():
		return 'volume'

	@classmethod
	def add_subparser(cls, command_parsers):
		parser = command_parsers.add_parser(cls.cmd(), help='Group of subcommands related to persistent volumes')
		subcommand_parsers = parser.add_subparsers(title='subcommands', dest='subcommand')

		# List
		parser_list = subcommand_parsers.add_parser('list', help='List persistent volumes')
		parser_list.add_argument('-a', '--all', dest='all', action='store_true',
								 help='Show all volumes, not only ones created by Portal Gun.')
		parser_list.set_defaults(actor=cls.list_volumes)

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
		parser_create.set_defaults(actor=cls.create_volume)
		# TODO: add silent mode

		# Update
		parser_update = subcommand_parsers.add_parser('update', help='Update persistent volume')
		parser_update.add_argument(dest='volume_id', help='Volume Id.')
		parser_update.add_argument('-n', '--name', dest='name', help='Update name of volume.')
		parser_update.add_argument('-s', '--size', dest='size', type=int, help='Update size of volume.')
		parser_update.add_argument('-t', '--tags', nargs='+', dest='tags', metavar='key:value',
								   help='Add user tags for volume.')
		parser_update.set_defaults(actor=cls.update_volume)

		# Delete
		parser_delete = subcommand_parsers.add_parser('delete', help='Delete persistent volume')
		parser_delete.add_argument(dest='volume_id', help='Volume Id.')
		parser_delete.add_argument('-f', '--force', dest='force', action='store_true',
								   help='Delete any volume, even not owned.')
		parser_delete.set_defaults(actor=cls.delete_volume)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		# Call corresponding actor to handle selected subcommand
		self._args.actor(self, aws, self._args)

	def list_volumes(self, aws, args):
		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			if not args.all:
				# Get current user
				with step('Get user identity'):
					user = aws.get_user_identity()

				# Get list of volumes owned by user
				with step('Get list of proper volumes'):
					volumes = aws.get_volumes(self.get_proper_volume_filter(user))
			else:
				# Get list of all volumes
				with step('Get list of volumes'):
					volumes = aws.get_volumes()

		# Filter tags of every volume
		volumes = (self.filter_tags(volume) for volume in volumes)

		# Pretty print list of volumes
		map(print_volume, volumes)

	def create_volume(self, aws, args):
		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Ensure that instance does not yet exist
			with step('Get Availability Zones'):
				availability_zones = aws.get_availability_zones()

		print('Creating new persistent volume.')

		# Get properties of the new volume
		name = args.name
		size = args.size
		availability_zone = args.zone
		snapshot_id = args.snapshot

		# Ask for name, if not provided
		if name is None:
			print('Enter name for the new volume (no name by default): ', end='')
			name = raw_input() or None

		# Ask for size, if not provide
		if args.size is None:
			print('Enter size of the new volume in Gb ({}): '.format(self._default_size), end='')
			size = raw_input() or self._default_size
			try:
				size = int(size)
			except ValueError as e:
				exit('Size has to be an integer.')

		# Check size parameter
		if size < self._min_size:
			exit('Specified size {}Gb is smaller than the lower limit of {}Gb.'.format(size, self._min_size))
		elif size > self._max_size:
			exit('Specified size {}Gb is bigger than the upper limit of {}Gb.'.format(size, self._max_size))

		# Ask for availability zone, if not provided
		if availability_zone is None:
			print('Enter availability zone for the new volume ({}): '.format(availability_zones[0]), end='')
			availability_zone = raw_input() or availability_zones[0]

		# Check availability zone
		if availability_zone not in availability_zones:
			exit('Unexpected availability zone "{}". Available zones are: {}.'
				 .format(availability_zone, ', '.join(availability_zones)))

		# Set tags
		tags = {'Name': name, 'created-by': user['Arn'], self._proper_tag_key: self._proper_tag_value}

		# Add user-specified tags, if provided
		if args.tags is not None:
			tags.update(self.parse_tags(args.tags))

		# Create volume
		volume_id = aws.create_volume(size, availability_zone, tags, snapshot_id)

		print('New persistent volume has been created.\nVolume id: {}'.format(volume_id))

	def update_volume(self, aws, args):
		updates = 0

		# Get user tags
		tags = self.parse_tags(args.tags)

		# Add 'Name' tag, if specified
		if args.name is not None:
			tags.update({'Name': args.name})

		# Update tags, if specified
		if len(tags) > 0:
			aws.add_tags(args.volume_id, tags)
			updates += len(tags)

		# Update size, if specified
		if args.size is not None:
			aws.update_volume(args.volume_id, args.size)
			updates += 1

		if updates > 0:
			print('Volume {} is updated.'.format(args.volume_id))
		else:
			print('Nothing to do.')

	def delete_volume(self, aws, args):
		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				user = aws.get_user_identity()

			# Ensure that instance does not yet exist
			with step('Get volume details'):
				volume = aws.get_volumes_by_id(args.volume_id)[0]

		if not self.is_proper_volume(volume, user) and not args.force:
			raise CommandError('Volume {} is not owned by you. Use -f flag to force deletion.'.format(args.volume_id))

		aws.delete_volume(args.volume_id)

		print('Volume {} is deleted.'.format(args.volume_id))

	def filter_tags(self, volume):
		if 'Tags' in volume:
			volume['Tags'] = [tag for tag in volume['Tags'] if tag['Key'] not in self._service_tags]

		return volume

	def parse_tags(self, tags):
		"""
		Parse tags from command line arguments.
		:param tags: List of tag args in 'key:value' format.
		:return: Tags in dictionary format
		"""
		return {key_value[0]: key_value[1] for key_value in
				(tag.split(':') for tag in (tags or []))
				if len(key_value) == 2 and len(key_value[0]) > 0 and len(key_value[1]) > 0}

	def is_proper_volume(self, volume, user):
		try:
			tags = from_aws_tags(volume['Tags'])
			return tags[self._proper_tag_key] == self._proper_tag_value and tags['created-by'] == user['Arn']
		except KeyError:
			return False

	def get_proper_volume_filter(self, user):
		return {'tag:{}'.format(self._proper_tag_key): self._proper_tag_value, 'tag:created-by': user['Arn']}
