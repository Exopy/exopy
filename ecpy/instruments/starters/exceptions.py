# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tool handling initializind/finalizing a driver.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


class InstrIOError(Exception):
    """Exception used by starters to report an IO error.

    """
    pass
