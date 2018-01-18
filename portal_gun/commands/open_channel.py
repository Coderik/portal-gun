from os import path
import json

from portal_gun.commands.base_command import BaseCommand
from portal_gun.configuration.validation import validate_portal_spec


class OpenChannelCommand(BaseCommand):
	def __init__(self, args):
		BaseCommand.__init__(self, args)

	def run(self):
		print('Running `{}` command.'.format(self.cmd()))

	@staticmethod
	def cmd():
		return 'channel'
