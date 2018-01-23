import argparse
import json
import logging
from sys import exit, stderr

from portal_gun.app import App
from portal_gun.commands import create_command


def main():
	# Parse command line arguments
	parser = argparse.ArgumentParser(prog='Portal Gun')
	parser.add_argument('command', help='command to execute')
	parser.add_argument('props', help='properties for command', nargs='*')
	parser.add_argument('-c', '--config', default='config.json', dest='config', help='configuration file')
	args = parser.parse_args()

	command = create_command(args.command, args)

	if command is None:
		exit('Unknown command "{}".'.format(args.command))

	command.run()

	# # Read config
	# try:
	# 	with open(args.config) as json_config_file:
	# 		config = json.load(json_config_file)
	# except IOError as e:
	# 	exit('Could not read config file: {}'.format(e))
	# except json.decoder.JSONDecodeError as e:
	# 	exit('Could not read config file: {}'.format(e))
	#
	# # Enable logging
	# logging.basicConfig(format=u'%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d \n\t %(message)s',
	# 					level=logging.INFO,
	# 					stream=stderr)
	# logger = logging.getLogger('Transcoding Service')
	#
	# app = App(logger)
	#
	# if app.configure(config):
	# 	app.run()
