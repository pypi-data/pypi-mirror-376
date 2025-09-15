# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['fede']
setup_kwargs = {
    'name': 'fede',
    'version': '0.1.0',
    'description': 'My CV',
    'long_description': 'None',
    'author': 'Fede Calendino',
    'author_email': 'federico@calendino.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/fedecalendino',
    'py_modules': modules,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
