import json

from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import googleapiclient.discovery

from portal_gun.providers.exceptions import ProviderRequestError


def gcp_api_caller():
	from functools import wraps

	def api_caller_decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except HttpError as e:
				content = json.loads(e.content)
				raise ProviderRequestError(content['error']['message'])

		return wrapper

	return api_caller_decorator


class GcpClient(object):
	def __init__(self, service_account_file, project, region):
		self._service_account_file = service_account_file
		self._project = project
		self._region = region
		self._gce_client = None

	@gcp_api_caller()
	def request_instance(self, props):
		response = self.gce_client().instances().insert(project=self._project, zone=self._region, body=props).execute()

		return response

	@gcp_api_caller()
	def get_instance(self, name):
		response = self.gce_client().instances().get(project=self._project, zone=self._region, instance=name) \
			.execute()

		return response

	@gcp_api_caller()
	def find_instance(self, name):
		flt = 'name = {}'.format(name)
		response = self.gce_client().instances().list(project=self._project, zone=self._region, filter=flt) \
			.execute()

		if 'items' not in response or len(response['items']) == 0:
			return None

		return response['items'][0]

	@gcp_api_caller()
	def delete_instance(self, name):
		response = self.gce_client().instances().delete(project=self._project, zone=self._region, instance=name) \
			.execute()

		return response

	@gcp_api_caller()
	def get_operation(self, name):
		response = self.gce_client().zoneOperations().get(project=self._project, zone=self._region, operation=name) \
			.execute()

		return response

	@gcp_api_caller()
	def cancel_instance_request(self, name):
		response = self.gce_client().instances().delete(project=self._project, zone=self._region, instance=name).execute()

		return response

	@gcp_api_caller()
	def get_volumes(self):
		response = self.gce_client().disks().list(project=self._project, zone=self._region).execute()

		return response['items']

	def gce_client(self):
		if self._gce_client is None:
			try:
				credentials = service_account.Credentials.from_service_account_file(self._service_account_file)
			except IOError as e:
				raise ProviderRequestError('Could not find service account file: {}'.format(e.filename))

			self._gce_client = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

		return self._gce_client
