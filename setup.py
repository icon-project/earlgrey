import sys
from importlib import import_module
from pathlib import Path

from setuptools import setup, find_packages

sys.path.insert(0, str(Path.cwd() / 'earlgrey'))
try:
    module = import_module('version')
    version = getattr(module, '__version__')
finally:
    sys.path = sys.path[1:]

extras_requires = {
    'test': ['pytest~=5.4.2', 'mock~=4.0.1']
}

setup_options = {
    'name': 'earlgrey',
    'description': 'Python AMQP RPC library',
    'long_description': open('README.md').read(),
    'long_description_content_type': 'text/markdown',
    'url': 'https://github.com/icon-project/earlgrey',
    'version': version,
    'author': 'ICON foundation',
    'packages': find_packages(),
    'license': "Apache License 2.0",
    'install_requires': list(open('requirements.txt')),
    'extras_require': extras_requires,
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
