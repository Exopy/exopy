# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Editor allowing to customize the execution parameters of a task.
"""
import enaml
with enaml.imports():
    from .editor import ExecutionEditor

__all__ = ['ExecutionEditor']
