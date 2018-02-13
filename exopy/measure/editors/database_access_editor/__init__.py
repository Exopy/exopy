# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Editor allowing to extend the accessibility of database entries.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
with enaml.imports():
    from .editor import DatabaseAccessEditor

__all__ = ['DatabaseAccessEditor']
