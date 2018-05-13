from portal_gun.commands.handlers.base_handler import BaseHandler
from portal_gun.providers.gcp.gcp_client import GcpClient
from portal_gun.providers.gcp.pretty_print import print_volume


class GcpHandler(BaseHandler):
	def __init__(self, config):
		super(GcpHandler, self).__init__(config)

	@staticmethod
	def provider_name():
		return 'gcp'

	@staticmethod
	def provider_long_name():
		return 'Google Cloud Platform'

	@staticmethod
	def generate_portal_spec():
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
		raise NotImplementedError('Every subclass of BaseHandler should implement get_ssh_details() method.')

	def list_volumes(self, args):
		# Create GCP client
		gcp = self._create_client()

		volumes = gcp.get_volumes()

		# Pretty print list of volumes
		map(print_volume, volumes)

	def create_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement create_volume() method.')

	def update_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement update_volume() method.')

	def delete_volume(self, args):
		raise NotImplementedError('Every subclass of BaseHandler should implement delete_volume() method.')

	def _create_client(self):
		assert self._config

		return GcpClient(self._config['service_account_file'], self._config['project'], self._config['region'])
