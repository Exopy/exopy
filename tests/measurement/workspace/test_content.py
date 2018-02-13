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
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml
import pytest

from exopy.testing.util import process_app_events

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.log.manifest import LogManifest
    from exopy.tasks.manifest import TasksManagerManifest


pytests_plugin = str('exopy.testing.measurement.fixtures'),


@pytest.fixture
def content_workbench(measurement_workbench, measurement, windows):
    """Create a measurement workspace.

    """
    measurement_workbench.register(UIManifest())
    measurement_workbench.register(LogManifest())
    measurement_workbench.register(TasksManagerManifest())
    measurement_plugin = measurement_workbench.get_plugin('exopy.measurement')
    measurement_plugin.selected_engine = 'dummy'
    measurement_plugin.default_monitors = ['dummy']

    return measurement_workbench


@pytest.mark.timeout(30)
def test_content(content_workbench, windows, dialog_sleep):
    """Test creating the content of the workspace.

    """
    w = content_workbench
    ui = w.get_plugin('enaml.workbench.ui')
    ui.show_window()
    process_app_events()
    sleep(dialog_sleep)

    core = content_workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})
    process_app_events()
    sleep(dialog_sleep)

    pl = content_workbench.get_plugin('exopy.measurement')
    pl.workspace.new_measurement()
    process_app_events()
    sleep(dialog_sleep)

    ui.close_window()
