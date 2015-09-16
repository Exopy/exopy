# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""All possible contributions to plugin of the app package.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from .dependencies import BuildDependency, RuntimeDependency

__all__ = ['BuildDependency', 'RuntimeDependency']
