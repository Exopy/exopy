# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Editors allow to customize the edition of the task hierarchy.

They can apply to all tasks or only to a subset, in the later case they are
only available when the task is selected.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from .base_editor import BaseEditor, Editor


__all__ = ['BaseEditor', 'Editor']
