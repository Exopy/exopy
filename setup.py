#!/usr/bin/env python
# --------------------------------------------------------------------------------------
# Copyright (c) 2015-2022, Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# --------------------------------------------------------------------------------------
from setuptools import setup, find_packages

import pathlib


def long_description():
    """Read the project description from the README file."""
    with (pathlib.Path(__file__).parent / "README.rst").open("r") as f:
        return f.read()


setup(
    name="exopy",
    description="Experiment control application",
    long_description=long_description(),
    author="Exopy Developers (see AUTHORS)",
    author_email="m.dartiailh@gmail.com",
    url="http://github.com/exopy/exopy",
    download_url="http://github.com/exopy/exopy/tarball/master",
    keywords="experiment automation GUI",
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    zip_safe=False,
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ["*.enaml", "*.txt"]},
    python_requires=">=3.8",
    install_requires=[
        "atom>=0.7.0",
        "enaml[qt5-pyqt]>=0.14.1",
        "configobj",
        "watchdog",
        "qtawesome",
        "numpy",
    ],
    entry_points={"gui_scripts": "exopy = exopy.__main__:main"},
)
