# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the measurement workspace content widget.

"""
import enaml
import pytest

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.log.manifest import LogManifest
    from exopy.tasks.manifest import TasksManagerManifest


pytests_plugin = str('exopy.testing.measurement.fixtures'),


@pytest.fixture
def content_workbench(measurement_workbench, measurement, exopy_qtbot):
    """Create a measure workspace.

    """
    measurement_workbench.register(UIManifest())
    measurement_workbench.register(LogManifest())
    measurement_workbench.register(TasksManagerManifest())
    measurement_plugin = measurement_workbench.get_plugin('exopy.measurement')
    measurement_plugin.selected_engine = 'dummy'
    measurement_plugin.default_monitors = ['dummy']

    return measurement_workbench


@pytest.mark.timeout(30)
def test_content(exopy_qtbot, content_workbench, dialog_sleep):
    """Test creating the content of the workspace.

    """
    w = content_workbench
    ui = w.get_plugin('enaml.workbench.ui')
    ui.show_window()
    exopy_qtbot.wait(10 + dialog_sleep)

    core = content_workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})
    exopy_qtbot.wait(10 + dialog_sleep)

    pl = content_workbench.get_plugin('exopy.measure')
    pl.workspace.new_measure()
    exopy_qtbot.wait(10 + dialog_sleep)

    ui.close_window()
