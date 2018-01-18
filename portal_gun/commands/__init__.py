import pkgutil

from portal_gun.commands.factory import create_command

# Expose factory method
__all__ = ['create_command']

# Make sure all subclasses of BaseCommand are imported
__path__ = pkgutil.extend_path(__path__, __name__)
for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
	__import__(modname)
