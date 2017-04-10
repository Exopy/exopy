# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility functions to generate well behaved tracebacks

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import sys

from future.utils.surrogateescape import register_surrogateescape
register_surrogateescape()

if sys.version_info >= (3,):
    from traceback import format_exc, format_tb
else:
    def format_exc():
        """Decode and format the current traceback in a safe way.

        """
        from traceback import format_exc
        return format_exc().decode('utf-8', 'surrogateescape')

    def format_tb(tb):
        """Format and decode a traceback in a safe way.

        """
        from traceback import format_tb
        return format_tb(tb).decode('utf-8', 'surrogateescape')

__all__ = ['format_exc', 'format_tb']
