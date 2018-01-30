.. _installation:

Installation
============

Compatibility
-------------

Ecpy is compatible with Python 2.7 and 3.4 or later.

Linux, Windows and OSX should all work as long as Qt 4 or Qt 5 is supported
by the platform.

Installing using Conda
----------------------

The easiest way to install ecpy and get updates is by using Conda,
a cross-platform package manager and software distribution maintained
by Continuum Analytics.  You can either use `Anaconda
<http://continuum.io/downloads.html>`_ to get the full stack in one download,
or `Miniconda <http://conda.pydata.org/miniconda.html>`_ which will install
the minimum packages needed to get started.

Once you have conda installed, just type::

   $ conda install -c ecpy ecpy

or::

   $ conda update -c ecpy ecpy
   
.. note::

    The -c option select the ecpy channel on <http://anaconda.org> as Ecpy is 
    not part of the standard Python stack.

Installing from source
----------------------

Ecpy itself is a pure python package and as such is quite easy to install from
source, to do so just use :

    $ pip install https://github.com/Ecpy/ecpy/tarball/master

The dependencies of Ecpy however can be more cumbersome to install. You can 
find the list in the setup.py script at the root of the Ecpy repository.

Checking your installation
--------------------------

You should then be able to start ecpy using the ecpy command in a command
line or the launcher present in the Anaconda Launcher if you are using 
Anaconda.

In case this does not work you can run the application from the command line 
using:

    $ python -m ecpy -s

This allows to display the error log directly in the console which should allow
you to track down the origin of the issue.
    
