import boto3

from portal_gun.commands.base_command import BaseCommand
from portal_gun.context_managers.pass_step_or_die import pass_step_or_die
from portal_gun.commands.helpers import run_preflight_steps
import portal_gun.aws_helpers as aws_helpers


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))
		print('\tPreflight checks:'.expandtabs(4))

		config, portal_spec, portal_name = run_preflight_steps(self._args)

		print('\tPreflight checks are complete.'.expandtabs(4))

		ec2_client = boto3.client('ec2',
								  config['aws_region'],
								  aws_access_key_id=config['aws_access_key'],
								  aws_secret_access_key=config['aws_secret_key'])

		# Make a request for Spot instance
		request_config = aws_helpers.single_instance_spot_fleet_request(portal_spec)
		response = ec2_client.request_spot_fleet(SpotFleetRequestConfig=request_config)

		print('Done')

	@staticmethod
	def cmd():
		return 'open'
