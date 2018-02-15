# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Measurement workspace fixture functions.

"""
import pytest
import enaml


with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.log.manifest import LogManifest
    from exopy.tasks.manifest import TasksManagerManifest


pytests_plugin = str('exopy.testing.measurement.fixtures'),


@pytest.yield_fixture
def workspace(measurement_workbench, measurement, windows):
    """Create a measurement workspace.

    """
    measurement_workbench.register(UIManifest())
    measurement_workbench.register(LogManifest())
    measurement_workbench.register(TasksManagerManifest())
    measurement_plugin = measurement_workbench.get_plugin('exopy.measurement')
    measurement_plugin.selected_engine = 'dummy'
    measurement_plugin.default_monitors = ['dummy']
    core = measurement_workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})

    yield measurement_plugin.workspace

    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})

    for m_id in ('exopy.tasks', 'exopy.app.logging'):
        try:
            measurement_workbench.unregister(m_id)
        except ValueError:
            pass
