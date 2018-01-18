from portal_gun.commands.base_command import BaseCommand


class OpenChannelCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running channel')

	@staticmethod
	def cmd():
		return 'channel'
