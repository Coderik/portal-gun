from portal_gun.commands.base_command import BaseCommand


class OpenPortalCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running open')

	@staticmethod
	def cmd():
		return 'open'
