# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the measure plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from exopy.testing.util import exit_on_err
from exopy.measure.measure import Measure
from exopy.tasks.api import RootTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from exopy.app.app_manifest import AppManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.dependencies.manifest import DependenciesManifest
    from exopy.app.icons.manifest import IconManagerManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.errors.plugin import ErrorsPlugin
    from exopy.app.states.manifest import StateManifest
    from exopy.measure.manifest import MeasureManifest
    from exopy.measure.monitors.text_monitor.manifest\
        import TextMonitorManifest

with enaml.imports():
    from .contributions import MeasureTestManifest


pytests_plugin = str('exopy.testing.fixtures'),


@pytest.yield_fixture
def measure_workbench(workbench, monkeypatch, app_dir):
    """Setup the workbench in such a way that the measure plugin can be tested.

    """
    monkeypatch.setattr(ErrorsPlugin, 'exit_error_gathering', exit_on_err)
    workbench.register(CoreManifest())
    workbench.register(AppManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())
    workbench.register(ErrorsManifest())
    workbench.register(DependenciesManifest())
    workbench.register(StateManifest())
    workbench.register(MeasureManifest())
    workbench.register(TextMonitorManifest())

    yield workbench

    for m_id in ('exopy.measure.monitors.text_monitor', 'exopy.measure',
                 'exopy.app.dependencies', 'exopy.app.errors',
                 'exopy.app.icons', 'exopy.app.preferences', 'exopy.app'):
        try:
            workbench.unregister(m_id)
        except ValueError:
            pass

        # Give some time to the os to release resources linked to file
        # monitoring.
        sleep(0.1)


@pytest.fixture
def measure(measure_workbench):
    """Register the dummy testing tools and create an empty measure.

    """
    try:
        measure_workbench.register(MeasureTestManifest())
    except ValueError:
        pass
    plugin = measure_workbench.get_plugin('exopy.measure')
    measure = Measure(plugin=plugin, root_task=RootTask(),
                      name='Dummy', id='001')
    return measure
