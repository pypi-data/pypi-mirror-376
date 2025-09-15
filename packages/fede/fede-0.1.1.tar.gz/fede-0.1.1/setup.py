# -*- coding: utf-8 -*-
from setuptools import setup

modules = \
['fede']
entry_points = \
{'console_scripts': ['fede = fede:main']}

setup_kwargs = {
    'name': 'fede',
    'version': '0.1.1',
    'description': 'My CV',
    'long_description': 'None',
    'author': 'Fede Calendino',
    'author_email': 'federico@calendino.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/fedecalendino',
    'py_modules': modules,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
