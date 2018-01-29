#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os.path
import sys

sys.path.insert(0, os.path.abspath('.'))
from ecpy.version import __version__


setup(
    name='ecpy',
    description='Experiment control application',
    version=__version__,
    long_description='',
    author='Ecpy Developers (see AUTHORS)',
    author_email='m.dartiailh@gmail.com',
    url='http://github.com/ecpy/ecpy',
    download_url='http://github.com/ecpy/ecpy/tarball/master',
    keywords='experiment automation GUI',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Physics',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'': ['*.enaml', '*.txt']},
    requires=['future', 'pyqt', 'atom', 'enaml', 'kiwisolver',
              'configobj', 'watchdog', 'setuptools', 'qtawesome',
              'numpy'],
    setup_requires=['setuptools'],
    install_requires=['setuptools', 'future', 'atom>=0.4.1',
                      'enaml>=0.10.2', 'kiwisolver>=1.0.0', 'configobj',
                      'watchdog', 'qtawesome', 'numpy'],
    entry_points={'gui_scripts': 'ecpy = ecpy.__main__:main'},
)
