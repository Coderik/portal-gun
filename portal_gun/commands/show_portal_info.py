from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands.base_command import BaseCommand
from portal_gun.commands.helpers import get_config, get_portal_spec
from portal_gun.context_managers.no_print import no_print
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.context_managers.print_scope import print_scope


class ShowPortalInfoCommand(BaseCommand):
	FIELDS = ['name', 'status', 'id', 'type', 'user', 'host', 'ip', 'remote', 'key']

	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'info'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Show information about portal')
		parser.add_argument('portal', help='Name of portal')
		parser.add_argument('-f', '--field', dest='field', help='Print value for a specified field ({}).'
							.format(', '.join(cls.FIELDS)))

	def run(self):
		if self._args.field is not None:
			# Get value of the specified field and print it
			value = self.get_field(self._args.field)
			if value is not None:
				print value
		else:
			self.show_full_info()

	def get_field(self, field):
		# Ensure field name is valid
		if field not in self.FIELDS:
			return None

		with no_print():
			# Find, parse and validate configs
			config, portal_spec, portal_name = get_portal_spec(self._args)

			if field == 'name':
				return portal_name
			if field == 'user':
				return portal_spec['spot_instance']['remote_user']
			if field == 'key':
				return portal_spec['spot_instance']['ssh_key_file']

			# Create AWS client
			aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

			# Get current user
			aws_user = aws.get_user_identity()

			# Get spot instance
			instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

			if field == 'status':
				return 'open' if instance_info is not None else 'close'

			# If portal is closed, we cannot provide any other information
			if instance_info is None:
				return None

			if field == 'id':
				return instance_info['InstanceId']
			if field == 'type':
				return instance_info['InstanceType']
			if field == 'host':
				return instance_info['PublicDnsName']
			if field == 'ip':
				return instance_info['PublicIpAddress']
			if field == 'remote':
				return '{}@{}'.format(portal_spec['spot_instance']['remote_user'], instance_info['PublicDnsName'])

		return None

	def show_full_info(self):
		print('Running `{}` command.\n'.format(self.cmd()))

		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with pass_step_or_die('User identity',
								  'Could not get current user identity'.format(portal_name)):
				aws_user = aws.get_user_identity()

			# Get spot instance
			with pass_step_or_die('Spot instance',
								  'Portal `{}` does not seem to be opened'.format(portal_name),
								  errors=[RuntimeError]):
				instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

		# Print status
		if instance_info is not None:
			with print_scope('Summary:', ''):
				print('Name:              {}'.format(portal_name))
				print('Status:            open')

			with print_scope('Instance:', ''):
				print('Id:                {}'.format(instance_info['InstanceId']))
				print('Type:              {}'.format(instance_info['InstanceType']))
				print('Public IP:         {}'.format(instance_info['PublicIpAddress']))
				print('Public DNS name:   {}'.format(instance_info['PublicDnsName']))
				print('User:              {}'.format(portal_spec['spot_instance']['remote_user']))

			with print_scope('Persistent volumes:', ''):
				for volume_spec in portal_spec['persistent_volumes']:
					print('{}: {}'.format(volume_spec['device'], volume_spec['mount_point']))

			# Print ssh command
			with print_scope('Use the following command to connect to the remote machine:'):
				print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
												 portal_spec['spot_instance']['remote_user'],
												 instance_info['PublicDnsName']))
		else:
			with print_scope('Summary:'):
				print('Name:              {}'.format(portal_name))
				print('Status:            close')
