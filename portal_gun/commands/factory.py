from portal_gun.commands.base_command import BaseCommand


def create_command(cmd, args):
	""" Convenient wrapper for factory method that creates Commands. """

	return BaseCommand.create_command(cmd, args)
