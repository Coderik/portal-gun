import pkgutil

from .factory import get_handler_class, create_handler


def generate_portal_spec(provider):
	"""
	Generates draft portal specification.
	:param provider: Name of cloud provider
	:rtype: dict
	"""
	handler_class = get_handler_class(provider)
	return handler_class.generate_portal_spec()

__all__ = [
	'create_handler',
	'generate_portal_spec'
]

# Make sure all subclasses of BaseHandler are imported
__path__ = pkgutil.extend_path(__path__, __name__)
for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
	__import__(modname)
