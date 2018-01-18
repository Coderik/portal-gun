from portal_gun.commands.base_command import BaseCommand


class ShowPortalStatusCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running status')

	@staticmethod
	def cmd():
		return 'status'
