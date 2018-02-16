# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""exopy.measurement.engines.process_engine :

Engine executing the measurement in a different process.

"""
import enaml
with enaml.imports():
    from .engine_declaration import ProcessEngine

__all__ = ['ProcessEngine']
