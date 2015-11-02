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

from time import sleep

import pytest
import enaml
from enaml.widgets.api import Window
from future.builtins import str

from ...util import process_app_events, handle_dialog

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from ecpy.app.log.manifest import LogManifest
    from ecpy.tasks.manager.manifest import TasksManagerManifest
    from ..contributions import Flags


@pytest.fixture
def workspace(measure_workbench, measure, windows):
    """Create a measure workspace.

    """
    measure_workbench.register(UIManifest())
    measure_workbench.register(LogManifest())
    measure_workbench.register(TasksManagerManifest())
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


@pytest.mark.timeout(10)
def test_creating_saving_loading_measure(workspace, monkeypatch, tmpdir):
    """Test creating, saving, loading a measure.

    """
    workspace.new_measure()
    measure = workspace.plugin.edited_measures.measures[-1]
    assert len(workspace.plugin.edited_measures.measures) == 2
    assert measure.monitors

    d = tmpdir.mkdir('measure_save')
    f = d.join('test')
    from ecpy.measure.workspace.workspace import FileDialogEx

    # Test handling an empty answer.
    @classmethod
    def get(*args, **kwargs):
        pass
    monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
    workspace.save_measure(measure)

    assert not d.listdir()

    # Test saving.
    @classmethod
    def get(*args, **kwargs):
        return str(f)
    monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
    workspace.save_measure(measure)
    sleep(0.1)

    f += '.meas.ini'
    assert f in d.listdir()
    f.remove()

    # Test saving on previously used file.
    workspace.save_measure(measure)
    assert f in d.listdir()

    f = d.join('test2.meas.ini')

    # Test saving as in a new file.
    @classmethod
    def get(*args, **kwargs):
        return str(f)
    monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
    workspace.save_measure(measure, False)

    assert f in d.listdir()

    # Test handling error in saving.
    from ecpy.measure.measure import Measure

    def r(s, m):
        raise Exception()

    monkeypatch.setattr(Measure, 'save', r)
    with handle_dialog():
        workspace.save_measure(measure)

    # Test loading and dialog reject.
    @classmethod
    def get(*args, **kwargs):
        pass
    monkeypatch.setattr(FileDialogEx, 'get_open_file_name', get)
    assert workspace.load_measure('file') is None

    # Test loading measure.
    @classmethod
    def get(*args, **kwargs):
        return str(f)
    monkeypatch.setattr(FileDialogEx, 'get_open_file_name', get)
    workspace.load_measure('file')

    assert len(workspace.plugin.edited_measures.measures) == 3
    m = workspace.plugin.edited_measures.measures[2]
    assert m.path == str(f)

    # Test handling loading error.
    @classmethod
    def r(cls, measure_plugin, path, build_dep=None):
        return None, {'r': 't'}

    monkeypatch.setattr(Measure, 'load', r)
    with handle_dialog():
        workspace.load_measure('file')

    with pytest.raises(NotImplementedError):
        workspace.load_measure('template')


def test_handling_all_tools_combinations(workspace):
    """Test creating all kind of tools as defaults, and handling errors for
    all.

    """
    plugin = workspace.plugin
    plugin.default_pre_hooks = ['dummy', 'none']
    plugin.default_monitors = ['dummy', 'none']
    plugin.default_post_hooks = ['dummy', 'none']

    workspace.new_measure()
    m = workspace.plugin.edited_measures.measures[-1]
    assert len(m.pre_hooks) == 2
    assert len(m.monitors) == 1
    assert len(m.post_hooks) == 1


@pytest.mark.timeout(10)
def test_enqueueing_and_reenqueueing_measure(workspace, monkeypatch, tmpdir):
    """Test enqueue a measure and re-enqueue it.

    """
    m = workspace.plugin.edited_measures.measures[0]
    m.root_task.default_path = str(tmpdir)
    from ecpy.measure.workspace.workspace import os
    m.add_tool('pre-hook', 'dummy')
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)

    def r(f):
        raise OSError()

    # Fail remove temp file. Seen in coverage.
    monkeypatch.setattr(os, 'remove', r)

    assert workspace.enqueue_measure(m)

    # Make sure runtimes are always released.
    m = workspace.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    # Check enqueued, status
    assert workspace.plugin.enqueued_measures.measures
    m2 = workspace.plugin.enqueued_measures.measures[0]
    assert m2.status == 'READY'

    # Test re-enqueuing
    m2.status = 'COMPLETED'
    from ecpy.measure.measure import Measure

    def e(m):
        m.name = 'R'
    monkeypatch.setattr(Measure, 'enter_edition_state', e)
    workspace.reenqueue_measure(m2)
    assert m2.name == 'R'
    assert m2.status == 'READY'


@pytest.mark.timeout(10)
def test_enqueueing_fail_runtime(workspace, monkeypatch):
    """Test enqueueing a measure for which runtimes cannot be collected.

    """
    m = workspace.plugin.edited_measures.measures[0]
    m.add_tool('pre-hook', 'dummy')
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', True)
    with handle_dialog():
        workspace.enqueue_measure(m)

    assert not workspace.plugin.enqueued_measures.measures

    # Make sure runtimes are always released.
    m = workspace.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    w = workspace.plugin.workbench
    d = w.get_manifest('test.measure')
    assert d.find('runtime_dummy2').called


@pytest.mark.timeout(10)
def test_enqueueing_fail_checks(workspace):
    """Test enqueueing a measure not passing the checks.

    """
    m = workspace.plugin.edited_measures.measures[0]
    with handle_dialog():
        workspace.enqueue_measure(m)

    assert not workspace.plugin.enqueued_measures.measures

    # Make sure runtimes are always released.
    m = workspace.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(10)
def test_enqueueing_abort_warning(workspace, monkeypatch, tmpdir):
    """Test aborting enqueueing because some checks raised warnings.

    """
    m = workspace.plugin.edited_measures.measures[0]
    m.root_task.default_path = str(tmpdir)
    from ecpy.measure.measure import Measure

    witness = []

    def check(*args, **kwargs):
        witness.append(None)
        return True, {'r': {'t': 's'}}
    monkeypatch.setattr(Measure, 'run_checks', check)

    with handle_dialog('reject'):
        workspace.enqueue_measure(m)

    # Make sure runtimes are always released.
    m = workspace.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert not workspace.plugin.enqueued_measures.measures

    assert witness


@pytest.mark.timeout(10)
def test_enqueuing_fail_reload(workspace, monkeypatch, tmpdir):
    """Test failing when reloading the measure after saving.

    """
    m = workspace.plugin.edited_measures.measures[0]
    m.root_task.default_path = str(tmpdir)
    from ecpy.measure.measure import Measure

    witness = []

    @classmethod
    def r(cls, measure_plugin, path, build_dep=None):
        witness.append(None)
        return None, {'r': 't'}
    monkeypatch.setattr(Measure, 'load', r)

    with handle_dialog():
        workspace.enqueue_measure(m)

    # Make sure runtimes are always released.
    m = workspace.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert not workspace.plugin.enqueued_measures.measures

    assert witness


@pytest.mark.timeout(10)
def test_measure_execution(workspace):
    """Test selecting a new engine if no engine is selected and that commands
    are piped to the processor.

    """
    from ecpy.measure.processor import MeasureProcessor
    from atom.api import Unicode

    class P(MeasureProcessor):

        called = Unicode()

        def start_measure(self, measure):
            self.called = 'start'

        def pause_measure(self):
            self.called = 'pause'

        def resume_measure(self):
            self.called = 'resume'

        def stop_measure(self, no_post_exec=False, force=False):
            self.called = 'stop'

        def stop_processing(self, no_post_exec=False, force=False):
            self.called = 'processing'

    workspace.plugin.processor = P()
    workspace.plugin.selected_engine = ''
    workspace.plugin.processor.continuous_processing = False

    # Test not selecting an engine.
    with handle_dialog('reject'):
        workspace.start_processing_measures()

    workspace.plugin.enqueued_measures.measures.append(
        workspace.plugin.edited_measures.measures[0])

    def set_eng(dialog):
        dialog.selected_decl = workspace.plugin._engines.contributions['dummy']

    with handle_dialog('accept', set_eng):
        workspace.start_processing_measures()

    assert workspace.plugin.processor.continuous_processing
    assert workspace.plugin.processor.called == 'start'

    workspace.plugin.enqueued_measures.measures = []
    with handle_dialog():
        workspace.start_processing_measures()

    workspace.plugin.processor.called = ''
    workspace.process_single_measure(None)
    assert not workspace.plugin.processor.continuous_processing
    assert workspace.plugin.processor.called == 'start'

    workspace.pause_current_measure()
    assert workspace.plugin.processor.called == 'pause'

    workspace.resume_current_measure()
    assert workspace.plugin.processor.called == 'resume'

    workspace.stop_current_measure()
    assert workspace.plugin.processor.called == 'stop'

    workspace.stop_processing_measures()
    assert workspace.plugin.processor.called == 'processing'


def test_remove_processed_measures(workspace):
    """Test removing already processed measures from enqueued ones.

    """
    states = ('SKIPPED', 'FAILED', 'COMPLETED', 'INTERRUPTED', 'READY',
              'RUNNING', 'PAUSING', 'PAUSED', 'RESUMING',
              'STOPPING', 'EDITING')

    for i, s in enumerate(states):
        workspace.new_measure()
        m = workspace.plugin.edited_measures.measures[-1]
        workspace.plugin.enqueued_measures.measures.append(m)
        m.status = s

    workspace.remove_processed_measures()

    for m in workspace.plugin.enqueued_measures.measures:
        assert m.status not in ('SKIPPED', 'FAILED', 'COMPLETED',
                                'INTERRUPTED')


def test_creating_measure_when_low_index_was_destroyed(workspace):
    """Test that adding an edited measure when a previous one panel was closed
    re-use the index.

    """
    workspace.new_measure()
    workspace.dock_area.find('meas_0').destroy()
    workspace.new_measure()  # Create a dock item for a missing index
    m = workspace.plugin.edited_measures.measures[-1]
    dock = [d for d in workspace.dock_area.dock_items()
            if getattr(d, 'measure', None) is m][0]
    assert dock.name == 'meas_0'
