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

pytest_plugins = ('exopy.testing.fixtures',
                  'exopy.testing.instruments.fixtures',
                  'exopy.testing.measurement.fixtures',
                  'exopy.testing.measurement.workspace.fixtures',
                  'exopy.testing.measurement.monitors.text_monitor.fixtures',
                  'exopy.testing.tasks.fixtures')

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ui: mark test involving ui display"
    )
