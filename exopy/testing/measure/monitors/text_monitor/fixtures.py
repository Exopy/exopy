# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixtures used to test text monitor related systems.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest


pytest_plugins = str('exopy.testing.measure.fixtures'),


@pytest.fixture
def text_monitor_workbench(windows, measure_workbench):
    """Register the text monitor manifest.

    """
    return measure_workbench
