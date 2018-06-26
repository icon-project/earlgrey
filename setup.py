#!/usr/bin/env python
from setuptools import setup, find_packages

with open('requirements.txt') as requirements:
    requires = list(requirements)

setup_options = {
    'name': 'EarlGrey',
    'description': 'Message Queue library using RabbitMQ',
    'author': 'ICON foundation',
    'packages': find_packages(),
    'license': "Apache License 2.0",
    'install_requires': requires,
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6.5'
    ]
}

setup(**setup_options)
