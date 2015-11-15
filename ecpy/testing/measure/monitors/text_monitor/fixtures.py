# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
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
import enaml

with enaml.imports():
    from ecpy.measure.monitors.text_monitor.manifest import TextMonitorManifest


pytest_plugins = str('ecpy.testing.measure.fixtures'),


@pytest.yield_fixture
def text_monitor_workbench(app, measure_workbench):
    """Register the text monitor manifest.

    """
    m = TextMonitorManifest()
    measure_workbench.register(m)

    yield measure_workbench

    measure_workbench.unregister(m.id)
