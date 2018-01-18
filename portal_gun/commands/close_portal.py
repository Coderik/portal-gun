from portal_gun.commands.base_command import BaseCommand


class ClosePortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running close')

	@staticmethod
	def cmd():
		return 'close'
