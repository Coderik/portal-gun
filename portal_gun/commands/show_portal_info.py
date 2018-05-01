from portal_gun.aws.aws_client import AwsClient
from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.helpers import get_config, get_portal_spec
from portal_gun.context_managers.no_print import no_print
from portal_gun.context_managers.print_scope import print_scope
from portal_gun.context_managers.step import step


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
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

			if field == 'name':
				return portal_name
			if field == 'user':
				return portal_spec['spot_instance']['remote_user']
			if field == 'key':
				return portal_spec['spot_instance']['identity_file']

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
		# Find, parse and validate configs
		with print_scope('Checking configuration:', 'Done.\n'):
			config = get_config(self._args)
			portal_spec, portal_name = get_portal_spec(self._args)

		# Create AWS client
		aws = AwsClient(config['aws_access_key'], config['aws_secret_key'], config['aws_region'])

		volumes = []
		with print_scope('Retrieving data from AWS:', 'Done.\n'):
			# Get current user
			with step('Get user identity'):
				aws_user = aws.get_user_identity()

			# Get spot instance
			with step('Get spot instance', error_message='Portal `{}` does not seem to be opened'.format(portal_name),
					  catch=[RuntimeError]):
				instance_info = aws.find_spot_instance(portal_name, aws_user['Arn'])

			# Get persistent volumes, if portal is opened
			if instance_info is not None:
				with step('Get volumes'):
					volume_ids = [volume['Ebs']['VolumeId']
								  for volume in instance_info['BlockDeviceMappings']
								  if not volume['Ebs']['DeleteOnTermination']]
					volumes = aws.get_volumes_by_id(volume_ids)

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
				for i in range(len(volumes)):
					volume = volumes[i]
					with print_scope('Volume #{}:'.format(i), ''):
						self.print_volume_info(volume)

			# Print ssh command
			with print_scope('Use the following command to connect to the remote machine:'):
				print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['identity_file'],
												 portal_spec['spot_instance']['remote_user'],
												 instance_info['PublicDnsName']))
		else:
			with print_scope('Summary:'):
				print('Name:              {}'.format(portal_name))
				print('Status:            close')

	def print_volume_info(self, volume):
		tags = volume['Tags'] if 'Tags' in volume else []

		# Look for specific tags
		name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), '')
		mount_point = next((tag['Value'] for tag in tags if tag['Key'] == 'mount-point'), 'n/a')

		print('Id:            {}'.format(volume['VolumeId']))
		print('Name:          {}'.format(name))
		print('Size:          {}Gb'.format(volume['Size']))
		print('Device:        {}'.format(volume['Attachments'][0]['Device']))
		print('Mount point:   {}'.format(mount_point))
