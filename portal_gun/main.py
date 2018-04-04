import argparse
from sys import exit

from portal_gun.commands import fill_subparsers, create_command
from portal_gun.context_managers.print_indent import PrintIndent


def main():
	# Parse command line arguments
	parser = argparse.ArgumentParser(prog='PortalGun')
	subparsers = parser.add_subparsers(title='commands', dest='command')

	# Add sub argparsers for commands
	fill_subparsers(subparsers)

	parser.add_argument('-c', '--config', default='config.json', dest='config', help='Configuration file')
	args = parser.parse_args()

	command = create_command(args.command, args)

	if command is None:
		exit('Unknown command "{}".'.format(args.command))

	command.run()
