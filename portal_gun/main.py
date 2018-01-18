import argparse
import logging
import json
from sys import exit, stderr

from portal_gun.app import App


def main():
	# Parse command line arguments
	parser = argparse.ArgumentParser(prog='Portal Gun')
	parser.add_argument('-c', '--config', default='config.json', dest='config', help='configuration file')
	args = parser.parse_args()

	# Read config
	try:
		with open(args.config) as json_config_file:
			config = json.load(json_config_file)
	except IOError as e:
		exit('Could not read config file: {}'.format(e))
	except json.decoder.JSONDecodeError as e:
		exit('Could not read config file: {}'.format(e))

	# Enable logging
	logging.basicConfig(format=u'%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d \n\t %(message)s',
						level=logging.INFO,
						stream=stderr)
	logger = logging.getLogger('Transcoding Service')

	app = App(logger)

	if app.configure(config):
		app.run()
