#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os.path
import sys

sys.path.insert(0, os.path.abspath('.'))
from exopy.version import __version__


def long_description():
    """Read the project description from the README file.

    """
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


setup(
    name='exopy',
    description='Experiment control application',
    version=__version__,
    long_description=long_description(),
    author='Exopy Developers (see AUTHORS)',
    author_email='m.dartiailh@gmail.com',
    url='http://github.com/exopy/exopy',
    download_url='http://github.com/exopy/exopy/tarball/master',
    keywords='experiment automation GUI',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Physics',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'': ['*.enaml', '*.txt']},
    python_requires='>=3.5',
    setup_requires=['setuptools'],
    install_requires=['atom>=0.4.1', 'enaml>=0.10.2',
                      'kiwisolver>=1.0.0', 'configobj',
                      'watchdog', 'qtawesome', 'numpy',
                      'pyqt5'],
    entry_points={'gui_scripts': 'exopy = exopy.__main__:main'},
)
