from google.oauth2 import service_account
import googleapiclient.discovery


class GcpClient(object):
	def __init__(self, service_account_file, project, region):
		self._service_account_file = service_account_file
		self._project = project
		self._region = region
		self._gce_client = None

	def get_volumes(self):
		response = self.gce_client().disks().list(project=self._project, zone=self._region).execute()

		return response['items']

	def gce_client(self):
		if self._gce_client is None:
			# scopes = ['https://www.googleapis.com/auth/sqlservice.admin']
			credentials = service_account.Credentials.from_service_account_file(self._service_account_file)

			self._gce_client = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

		return self._gce_client
