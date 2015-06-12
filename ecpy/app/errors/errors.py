# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin centralizing the application error handling.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode
from enaml.core.api import Declarative, d_, d_func


class ErrorHandler(Declarative):
    """
    """
    id = d_(Unicode())

    @d_func
    def handle(self, **kwargs):
        """
        """
        raise NotImplementedError()
