class BaseHandler(object):
	""" Base class for all specific Handlers. """
	def __init__(self):
		pass

	def generate_portal_spec(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement generate_portal_spec() method.')

	def open_portal(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement open_portal() method.')

	def close_portal(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement close_portal() method.')

	def show_portal_info(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement show_portal_info() method.')

	def get_portal_info_field(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement get_portal_info_field() method.')

	def get_ssh_details(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement get_ssh_details() method.')

	def list_volumes(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement list_volumes() method.')

	def create_volume(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement create_volume() method.')

	def update_volume(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement update_volume() method.')

	def delete_volume(self):
		raise NotImplementedError('Every subclass of BaseHandler should implement delete_volume() method.')
