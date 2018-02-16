.. _style_guide:

Style guide
===========

The uniformity of the coding style in a large project is of paramount
importance to make maintenance easier. Ecpy follows closely PEP8
recommendations which can be found here (`PEP8`_). One can automatically
format code using the autopep8 tool. Some of those rules and some additional
remarks are detailed below.

.. _PEP8: https://www.python.org/dev/peps/pep-0008/

.. contents::

Header
------

All files part of the Exopy should start with the following header :

.. code-block:: python

	# -*- coding: utf-8 -*-
	# -----------------------------------------------------------------------------
	# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
	#
	# Distributed under the terms of the BSD license.
	#
	# The full license is in the file LICENCE, distributed with this software.
	# -----------------------------------------------------------------------------

New contributors should add their name to the AUTHORS file at the root of the
project.

Immediately following this header one should find the module docstring.


Line length
-----------

`PEP8`_ specifies that lines should at most 79 characters long and this
rule is strictly enforced throughout Exopy (in code and in comments).
This makes the code much easier to read and on work on (one does not have to
resize its editor window to accommodate long lines).

Backslashes should be used sparingly. To write an expression on multiple lines
the preferred method should be to surround it with parenthesis.

.. note::

	Long strings can use triple quotes or the following trick to avoid
	indentation issues :

	.. code-block:: python

		msg = ('A very very long string, taking much more than a single line '
			   'to write.')

	The Python interpreter will automatically concatenate both strings when
	reading the file. Please that it will not insert any space or line feed
	(hence the space after 'line').


Docstrings
----------

All functions, classes and methods should have a docstring (even private
methods). Exopy use the `Numpy-style`_ docstrings which are human readable.

As most classes inherits from Atom and must therefore declare explicitly their
members, those should be documented using a comment above them starting by
'#:'. This makes the code easier to read than using the 'Attributes' section in
the docstring and is picked up by the API documentation generator.


.. _Numpy-style: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt


Naming conventions
------------------

The naming conventions taken from PEP8 specifications are the following :

- local variables and functions should have all lowercase names and use '\_' to
  separate different words. ex : my_variable
- class names should start with a capital letter and each new word should also
  start with one. ex : MyClass
- private variables or methods should start with a single '\_'
- module constants should be in uppercase and use '\_' to separate different
  words. ex : MY_CONSTANT


Import formatting
-----------------

Imports should be at the top of the file (after the module docstring) save in
special cases. They should be group as follow (each group separated from the
following by a blank line) :

- special imports for Python 2/3 compatibility
- standard library imports
- third parties libraries imports
- relative imports

In each section the 'import x' stements should always come before the
'from a import b' statements.

Imports of .enaml files should come after any other imports.


Python version compatibility
----------------------------

Ecpy supports Python 3.5 and 3.6. For the time being, it relies on a fork of
enaml, but this fork should be merged back in the master branch in the coming
months.
