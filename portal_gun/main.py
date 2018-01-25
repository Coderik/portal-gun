import argparse
from sys import exit

from portal_gun.commands import fill_subparsers, create_command


def main():
	# Parse command line arguments
	parser = argparse.ArgumentParser(prog='Portal Gun')
	subparsers = parser.add_subparsers(title='commands', dest='command')

	# Add sub argparsers for commands
	fill_subparsers(subparsers)

	parser.add_argument('-c', '--config', default='config.json', dest='config', help='configuration file')
	args = parser.parse_args()

	command = create_command(args.command, args)

	if command is None:
		exit('Unknown command "{}".'.format(args.command))

	command.run()
