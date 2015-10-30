# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test measure workspace capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from enaml.widgets.api import Window

from ...util import process_app_events

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from ecpy.app.log.manifest import LogManifest


@pytest.fixture
def workspace(measure_workbench, measure, windows):
    """Create a measure workspace.

    """
    measure_workbench.register(UIManifest())
    measure_workbench.register(LogManifest())
    measure_plugin = measure_workbench.get_plugin('ecpy.measure')
    measure_plugin.selected_engine = 'dummy'
    measure_plugin.default_monitors = ['dummy']
    core = measure_workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'ecpy.measure.workspace'})

    return measure_plugin.workspace


def test_workspace_lifecycle(workspace):
    """Test the workspace life cycle.

    """
    process_app_events()

    workbench = workspace.plugin.workbench
    log = workbench.get_plugin('ecpy.app.logging')
    # Check UI creation
    assert workspace.content
    assert workspace.dock_area
    assert workbench.get_manifest('ecpy.measure.workspace.menus')

    # Check log handling
    assert 'ecpy.measure.workspace' in log.handler_ids

    # Check engine handling
    engine = workbench.get_manifest('test.measure').find('dummy_engine')
    assert engine.workspace_contributing

    # Check measure creation
    assert len(workspace.plugin.edited_measures.measures) == 1
    assert workspace.plugin.edited_measures.measures[0].monitors

    # Check observance of engine selection.
    workspace.plugin.selected_engine = ''
    assert not engine.workspace_contributing
    workspace.plugin.selected_engine = 'dummy'

    # Test stopping the workspace
    core = workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'ecpy.measure.workspace'})

    assert workspace.plugin.workspace is None
    assert not engine.workspace_contributing
    assert workbench.get_manifest('ecpy.measure.workspace.menus') is None
    assert 'ecpy.measure.workspace' not in log.handler_ids

    # Test restarting now that we have one edited measure.
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'ecpy.measure.workspace'})
    assert len(workspace.plugin.edited_measures.measures) == 1

    # Create a false monitors_window
    workspace.plugin.processor.monitors_window = Window()
    workspace.plugin.processor.monitors_window.show()
    process_app_events()

    # Stop again
    core = workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'ecpy.measure.workspace'})
    process_app_events()

    assert not workspace.plugin.processor.monitors_window.visible


def test_creating_saving_loading_measure(workspace):
    pass


def test_handling_all_tools_combinations(workspace):
    pass


def test_enqueueing_and_reenqueueing_measure(workspace):
    pass


def test_measure_execution(workspace):
    pass
