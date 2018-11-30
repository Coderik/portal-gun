class BaseHandler(object):
	""" Base class for all specific Handlers. """
	def __init__(self, config):
		self._config = config

	@staticmethod
	def provider_name():
		""" Short name uniquely identifying cloud provider """
		raise NotImplementedError('Every subclass of BaseHandler should implement static provider_name() method.')

	@staticmethod
	def provider_long_name():
		""" Human-readable descriptive name of cloud provider """
		raise NotImplementedError('Every subclass of BaseHandler should implement static provider_long_name() method.')

	@staticmethod
	def generate_portal_spec():
		"""
		Generate draft of portal specification in dictionary format.
		:rtype dict
		"""
		raise NotImplementedError('Every subclass of BaseHandler should implement static generate_portal_spec() method.')

	def open_portal(self, portal_spec, portal_name):
		raise NotImplementedError('Every subclass of BaseHandler should implement open_portal() method.')

	def close_portal(self, portal_spec, portal_name):
		raise NotImplementedError('Every subclass of BaseHandler should implement close_portal() method.')

	def show_portal_info(self, portal_spec, portal_name):
		raise NotImplementedError('Every subclass of BaseHandler should implement show_portal_info() method.')

	def get_portal_info_field(self, portal_spec, portal_name, field):
		raise NotImplementedError('Every subclass of BaseHandler should implement get_portal_info_field() method.')

	def get_ssh_params(self, portal_spec, portal_name):
		"""
		Get parameters for ssh connection
		:param portal_spec:
		:param portal_name:
		:return: (identity file, remote user, host, disable_known_hosts)
		:rtype (str, str, str, bool)
		"""
		raise NotImplementedError('Every subclass of BaseHandler should implement get_ssh_details() method.')

	def list_volumes(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement list_volumes() method.')

	def create_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement create_volume() method.')

	def update_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement update_volume() method.')

	def delete_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement delete_volume() method.')
