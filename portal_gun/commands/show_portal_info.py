import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.context_managers.no_print import NoPrint
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.commands.aws_client import AwsClient


class ShowPortalInfoCommand(BaseCommand):
	FIELDS = ['name', 'status', 'id', 'type', 'user', 'host', 'ip', 'remote', 'key']

	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'info'

	@classmethod
	def add_subparser(cls, subparsers):
		parser = subparsers.add_parser(cls.cmd(), help='Show portal status')
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

		with NoPrint():
			# Find, parse and validate configs
			config, portal_spec, portal_name = run_preflight_steps(self._args)

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
		print('Make preflight checks:')
		config, portal_spec, portal_name = run_preflight_steps(self._args)
		print('Preflight checks are complete.\n')

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		print('Retrieve associated resources:')

		# Get current user
		with pass_step_or_die('User identity',
							  'Could not get current user identity'.format(portal_name)):
			aws_user = aws.get_user_identity()

		# Get spot instance
		with pass_step_or_die('Spot instance',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

		print('Done.\n')

		# Print status
		if instance_info is not None:
			print('Summary:')
			print('\tName:              {}'.format(portal_name).expandtabs(4))
			print('\tStatus:            open'.expandtabs(4))
			print('')

			print('Instance:'.expandtabs(4))
			print('\tId:                {}'.format(instance_info['InstanceId']).expandtabs(4))
			print('\tType:              {}'.format(instance_info['InstanceType']).expandtabs(4))
			print('\tPublic IP:         {}'.format(instance_info['PublicIpAddress']).expandtabs(4))
			print('\tPublic DNS name:   {}'.format(instance_info['PublicDnsName']).expandtabs(4))
			print('\tUser:              {}'.format(portal_spec['spot_instance']['remote_user']).expandtabs(4))
			print('')

			print('Persistent volumes:'.expandtabs(4))
			for volume_spec in portal_spec['persistent_volumes']:
				print('\t{}: {}'.format(volume_spec['device'], volume_spec['mount_point']).expandtabs(4))

			# Print ssh command
			print('')
			print('Use the following command to connect to the remote machine:')
			print('\tssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
											 portal_spec['spot_instance']['remote_user'],
											 instance_info['PublicDnsName']).expandtabs(4))
		else:
			print('Summary:')
			print('\tName:              {}'.format(portal_name).expandtabs(4))
			print('\tStatus:            close'.expandtabs(4))
