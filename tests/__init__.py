# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fix sys.path to run test locally.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import sys

# Try to run against an installed version otherwise add path to sys.path
try:
    import ecpy
    del ecpy
except ImportError:
    sys.path.append('..')
