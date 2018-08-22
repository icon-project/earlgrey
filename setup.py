#!/usr/bin/env python
from setuptools import setup, find_packages
from earlgrey import __version__

setup_options = {
    'name': 'earlgrey',
    'description': 'Python AMQP RPC library',
    'long_description': open('README.md').read(),
    'long_description_content_type': 'text/markdown',
    'url': 'https://github.com/icon-project/earlgrey',
    'version': __version__,
    'author': 'ICON foundation',
    'packages': find_packages(),
    'license': "Apache License 2.0",
    'install_requires': list(open('requirements.txt')),
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
}

setup(**setup_options)
