from .base_handler import BaseHandler


def get_handler_class(provider_name):
	"""
	Find appropriate Handler class for given cloud provider.
	:param provider_name: Name of cloud provider
	:rtype: type
	"""

	for cls in BaseHandler.__subclasses__():
		if cls.provider_name() == provider_name:
			return cls

	raise Exception('Unknown cloud provider: {}'.format(provider_name))


def create_handler(provider_name, config):
	"""
	Factory method that creates instances of Handlers.
	:param provider_name: Name of cloud provider
	:param config: Cloud provider config
	:return: Subclass of BaseHandler
	"""

	handler_class = get_handler_class(provider_name)
	return handler_class(config)


def list_providers():
	"""
	Get list of names of all supported cloud providers
	:rtype: list
	"""

	return [cls.provider_name() for cls in BaseHandler.__subclasses__()]


def describe_providers():
	"""
	Get list of descriptions of all supported cloud providers.
	Description includes fields: 'name', 'long_name'.
	:rtype: list
	"""

	return [
		{
			'name': cls.provider_name(),
			'long_name': cls.provider_long_name()
		}
		for cls in BaseHandler.__subclasses__()
	]
