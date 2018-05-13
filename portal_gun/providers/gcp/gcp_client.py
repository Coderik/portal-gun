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
