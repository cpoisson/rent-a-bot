"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Long description of the project is in the README.md
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(

    # Rent-A-Bot Package General Information

    name='rent-a-bot',

    version='0.0.1',

    description='Rent-A-Bot, your automation resource provider.',
    long_description=long_description,

    url='https://github.com/cpoisson/rent-a-bot',

    author='Charles Poisson',
    author_email='charles.poisson(at)gmail.com',

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
                      'pyyaml'],

    setup_requires=['pytest-runner'],

    tests_require=['pytest', 'pytest-cov'],

    extras_require={
        'dev': ['pytest', 'pytest-cov'],
        'test': ['pytest', 'pytest-cov'],
    },

    # Include files listed in the MANIFEST.in file of the repository
    include_package_data=True,

)
