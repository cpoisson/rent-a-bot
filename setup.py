# -*- coding: utf-8 -*-
"""
Rent-A-Bot
----------

Rent-A-Bot, your automation resource provider!

Rent-A-Bot is designed to help you lock your resources in your automation infrastructure.

Setup
`````
.. code:: bash
    $ pip install rent-a-bot
    $ export FLASK_APP=rentabot
    $ export RENTABOT_RESOURCE_DESCRIPTOR=path/to/your/descriptor
    $ flask run

Links
`````
* `website <https://github.com/cpoisson/rent-a-bot>`_

"""

from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))

setup(

    # Rent-A-Bot Package General Information

    name='rent-a-bot',

    version='0.0.6',

    description='Rent-A-Bot, your automation resource provider.',
    long_description=__doc__,

    url='https://github.com/cpoisson/rent-a-bot',

    author='Charles Poisson',
    author_email='charles.poisson@gmail.com',

    license='MIT',

    # Classifiers => https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Framework :: Flask',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],

    keywords='Resource allocation application for automation',

    packages=find_packages(exclude=['tests']),

    # Run time Requirements
    install_requires=['flask',
                      'flask-sqlalchemy',
                      'pyyaml',
                      'daiquiri'],

    setup_requires=['pytest-runner'],

    tests_require=['pytest', 'pytest-cov'],

    extras_require={
        'dev': ['pytest', 'pytest-cov'],
        'test': ['pytest', 'pytest-cov'],
    },

    # Include files listed in the MANIFEST.in file of the repository
    include_package_data=True,

)
