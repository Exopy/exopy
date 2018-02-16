# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Pytest fixtures.

"""
import os
from enaml.qt import QT_API
os.environ.setdefault('PYTEST_QT_API', QT_API)

pytest_plugins = str('exopy.testing.fixtures'),
