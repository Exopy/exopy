# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Measure workspace fixture functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


import pytest
import enaml


with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.log.manifest import LogManifest
    from exopy.tasks.manifest import TasksManagerManifest


pytests_plugin = str('exopy.testing.measure.fixtures'),


@pytest.yield_fixture
def workspace(measure_workbench, measure, windows):
    """Create a measure workspace.

    """
    measure_workbench.register(UIManifest())
    measure_workbench.register(LogManifest())
    measure_workbench.register(TasksManagerManifest())
    measure_plugin = measure_workbench.get_plugin('exopy.measure')
    measure_plugin.selected_engine = 'dummy'
    measure_plugin.default_monitors = ['dummy']
    core = measure_workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measure.workspace'})

    yield measure_plugin.workspace

    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measure.workspace'})

    for m_id in ('exopy.tasks', 'exopy.app.logging'):
        try:
            measure_workbench.unregister(m_id)
        except ValueError:
            pass
