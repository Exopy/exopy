# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the measure plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from pprint import pformat

import enaml

from ecpy.testing.util import ErrorDialogException

from ecpy.measure.measure import Measure
from ecpy.tasks.api import RootTask

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest
    from ecpy.app.icons.manifest import IconManagerManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.errors.plugin import ErrorsPlugin
    from ecpy.app.states.manifest import StateManifest
    from ecpy.measure.manifest import MeasureManifest
    from ecpy.measure.monitors.text_monitor.manifest import TextMonitorManifest

with enaml.imports():
    from .contributions import MeasureTestManifest


pytests_plugin = str('ecpy.testing.fixtures'),


@pytest.yield_fixture
def measure_workbench(workbench, monkeypatch, app_dir):
    """Setup the workbench in such a way that the measure plugin can be tested.

    """
    def exit_err(self):
        self._gathering_counter -= 1
        if self._gathering_counter < 1:
            self._gathering_counter = 0
            if self._delayed:
                msg = 'Unexpected exceptions occured :\n'
                raise ErrorDialogException(msg + pformat(self._delayed))

    monkeypatch.setattr(ErrorsPlugin, 'exit_error_gathering', exit_err)
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

    for m_id in ('ecpy.measure.monitors.text_monitor', 'ecpy.measure',
                 'ecpy.app.dependencies', 'ecpy.app.errors',
                 'ecpy.app.icons', 'ecpy.app.preferences', 'ecpy.app'):
        try:
            workbench.unregister(m_id)
        except ValueError:
            pass


@pytest.fixture
def measure(measure_workbench):
    """Register the dummy testing tools and create an empty measure.

    """
    try:
        measure_workbench.register(MeasureTestManifest())
    except ValueError:
        pass
    plugin = measure_workbench.get_plugin('ecpy.measure')
    measure = Measure(plugin=plugin, root_task=RootTask(),
                      name='Dummy', id='001')
    return measure
