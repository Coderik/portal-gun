import argparse
from sys import exit

from portal_gun import __version__
from portal_gun.commands import fill_subparsers, create_command
from portal_gun.commands.exceptions import CommandError
from portal_gun.context_managers.step import StepError
from portal_gun.aws.exceptions import AwsRequestError


def main():
	# Parse command line arguments
	parser = argparse.ArgumentParser(prog='PortalGun')
	subparsers = parser.add_subparsers(title='commands', dest='command')

	# Add sub argparsers for commands
	fill_subparsers(subparsers)

	parser.add_argument('-c', '--config', default=None, dest='config',
						help='set name and location of configuration file')
	parser.add_argument('--version', action='version', version=__version__)
	args = parser.parse_args()

	command = create_command(args.command, args)

	if command is None:
		exit('Unknown command: {}'.format(args.command))

	try:
		command.run()
	except (CommandError, StepError, AwsRequestError) as e:
		print('{}'.format(e).expandtabs(4))
