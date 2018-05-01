"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
import re

here = path.abspath(path.dirname(__file__))

# Get version
with open(path.join(here, 'portal_gun/__init__.py')) as f:
    version = re.search("^__version__ = '(\d\.\d+\.\d+(\.?(dev|a|b|rc)\d?)?)'$", f.read(), re.M).group(1)

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
	name='portal-gun',
    version=version,
    description=('A command line tool that automates repetitive tasks '
				 'associated with the management of Spot Instances on Amazon EC2 service.'),
    long_description=long_description,
	long_description_content_type='text/x-rst',
    url='https://github.com/Coderik/portal-gun',
    author='Vadim Fedorov',
    author_email='coderiks@gmail.com',
	license='MIT',
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
		'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=()),
    install_requires=[
		'boto3>=1.5.18',
		'Fabric>=1.14.0',
		'marshmallow>=3.0.0b8'
	],
    entry_points={  # Optional
        'console_scripts': [
            'portal=portal_gun.main:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/Coderik/portal-gun/issues',
        'Source': 'https://github.com/Coderik/portal-gun',
    },
	# keywords='words separated by whitespace',
	# package_data={
    #     'sample': ['package_data.dat'],
    # },
)
