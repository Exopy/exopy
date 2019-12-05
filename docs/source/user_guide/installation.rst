.. _installation:

Installation
============

Compatibility
-------------

Exopy is compatible with Python 3.4 or later.

Linux, Windows and OSX should all work as long as Qt 4 or Qt 5 is supported
by the platform.

Installing using Conda
----------------------

The easiest way to install exopy and get updates is by using Conda,
a cross-platform package manager and software distribution maintained
by Continuum Analytics.  You can either use `Anaconda
<http://continuum.io/downloads.html>`_ to get the full stack in one download,
or `Miniconda <http://conda.pydata.org/miniconda.html>`_ which will install
the minimum packages needed to get started.

Once you have conda installed, just type::

   $ conda install -c exopy exopy

or::

   $ conda update -c exopy exopy

.. note::

    The -c option select the exopy channel on <http://anaconda.org> as Exopy is
    not part of the standard Python stack.

Installing from source
----------------------

Exopy itself is a pure python package and as such is quite easy to install from
source, to do so just use :

    $ pip install https://github.com/Exopy/exopy/tarball/master

The dependencies of Exopy however can be more cumbersome to install. You can
find the list in the setup.py script at the root of the Exopy repository.

Checking your installation
--------------------------

You should then be able to start exopy using the exopy command in a command
line or the launcher present in the Anaconda Launcher if you are using
Anaconda.

In case this does not work you can run the application from the command line
using:

    $ python -m exopy -s

This allows to display the error log directly in the console which should allow
you to track down the origin of the issue.

