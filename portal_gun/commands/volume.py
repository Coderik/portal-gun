from __future__ import print_function

from portal_gun.aws.aws_client import AwsClient
from portal_gun.aws.exceptions import AwsRequestError
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config
from portal_gun.helpers.pretty_print import print_volume
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die


class VolumeCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

		self._default_size = 50
		self._min_size = 1  # Gb
		self._max_size = 16384  # Gb

	@staticmethod
	def cmd():
		return 'volume'

	@classmethod
	def add_subparser(cls, command_parsers):
		parser = command_parsers.add_parser(cls.cmd(), help='Perform operations with persistent volumes')
		subcommand_parsers = parser.add_subparsers(title='subcommands', dest='subcommand')

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

		parser_list = subcommand_parsers.add_parser('list', help='List volumes')
		parser_list.set_defaults(actor=cls.list_volumes)
		# TODO: add option to list all, list only created by Portal Gun by default

		# TODO: add set-name (or rename), delete subcommands

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

		# Find, parse and validate configs
		print('Checking configuration:')
		config = get_config(self._args)
		print('Done.\n')

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		# Call corresponding actor to handle selected subcommand
		self._args.actor(self, aws, self._args)

	def list_volumes(self, aws, args):
		try:
			volumes = aws.get_volumes()
		except AwsRequestError as e:
			exit('Error: {}'.format(e))

		map(print_volume, volumes)

	def create_volume(self, aws, args):
		print('Requesting data from AWS:')

		# Get current user
		with pass_step_or_die('Get user identity', 'Could not get current user identity', errors=[AwsRequestError]):
			user = aws.get_user_identity()

		# Ensure that instance does not yet exist
		with pass_step_or_die('Get Availability Zones', 'Could not get Availability Zones', errors=[AwsRequestError]):
			availability_zones = aws.get_availability_zones()

		print('Done.\n')

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
		tags = {'Name': name, 'created-by': user['Arn'], 'dimension': 'C-137'}

		# Add user-specified tags, if provided
		if args.tags is not None:
			tags.update({key_value[0]: key_value[1] for key_value in
						 [tag.split(':') for tag in args.tags]
						 if len(key_value) == 2 and len(key_value[0]) > 0 and len(key_value[1]) > 0})

		# Create volume
		volume_id = aws.create_volume(size, availability_zone, tags, snapshot_id)

		print('New persistent volume has been created.\nVolume id: {}'.format(volume_id))
