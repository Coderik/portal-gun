import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands.helpers import run_preflight_steps
from portal_gun.commands.aws_client import AwsClient


class ShowPortalStatusCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	@staticmethod
	def cmd():
		return 'status'

	def run(self):
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
			user = aws.get_user_identity()

		# Get spot instance
		with pass_step_or_die('Spot instance',
							  'Portal `{}` does not seem to be opened'.format(portal_name),
							  errors=[RuntimeError]):
			instance_info = aws.find_spot_instance(portal_name, user['Arn'])

		print('Done.\n')

		# Print status
		if instance_info is not None:
			# Print summary
			print('Portal `{}` is opened.'.format(portal_name).expandtabs(4))
			print('Summary:')
			print('\tInstance:'.expandtabs(4))
			print('\t\tId:              {}'.format(instance_info['InstanceId']).expandtabs(4))
			print('\t\tType:            {}'.format(instance_info['InstanceType']).expandtabs(4))
			print('\t\tPublic IP:       {}'.format(instance_info['PublicIpAddress']).expandtabs(4))
			print('\t\tPublic DNS name: {}'.format(instance_info['PublicDnsName']).expandtabs(4))
			print('\tPersistent volumes:'.expandtabs(4))
			for volume_spec in portal_spec['persistent_volumes']:
				print('\t\t{}: {}'.format(volume_spec['device'], volume_spec['mount_point']).expandtabs(4))

			# Print ssh command
			print('')
			print('Use the following command to connect to the remote machine:')
			print('ssh -i "{}" {}@{}'.format(portal_spec['spot_instance']['ssh_key_file'],
											 portal_spec['spot_instance']['remote_user'],
											 instance_info['PublicDnsName']))
		else:
			print('Portal `{}` is not opened.'.format(portal_name).expandtabs(4))
