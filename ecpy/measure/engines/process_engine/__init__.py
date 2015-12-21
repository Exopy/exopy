# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""ecpy.measure.engines.process_engine :

Engine executing the measure in a different process.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
with enaml.imports():
    from .engine_declaration import ProcessEngine

__all__ = ['ProcessEngine']
