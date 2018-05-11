from sys import argv
from os import path

default_config_filename = 'config.json'

# Paths where to look up for config file. Order reflects priority (from higher to lower)
config_paths = [
	path.join(path.dirname(path.abspath(argv[0])), default_config_filename),
	path.expanduser('~/.portal-gun/{}'.format(default_config_filename))
]

cloud_provider_env = 'PG_CLOUD_PROVIDER'
