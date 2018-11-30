import pkgutil

from portal_gun.commands.base_command import BaseCommand


def fill_subparsers(subparsers):
	""" Convenient wrapper for method that fills subparsers. """
	return BaseCommand.fill_subparsers(subparsers)


def create_command(cmd, args):
	""" Convenient wrapper for factory method that creates Commands. """
	return BaseCommand.create_command(cmd, args)

# Expose factory method
__all__ = [
	'fill_subparsers',
	'create_command'
]

# Make sure all subclasses of BaseCommand are imported
__path__ = pkgutil.extend_path(__path__, __name__)
for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
	__import__(modname)
