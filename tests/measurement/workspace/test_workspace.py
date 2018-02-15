# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Ditextibuted under the terms of the BSD license.
#
# The full license is in the file LICENCE, ditextibuted with this software.
# -----------------------------------------------------------------------------
"""Test measurement workspace capabilities.

"""
import pytest
import enaml
from enaml.widgets.api import Window

from exopy.testing.util import handle_dialog, ObjectTracker

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest
    from enaml.stdlib.message_box import MessageBox
    from exopy.app.log.manifest import LogManifest
    from exopy.tasks.manifest import TasksManagerManifest
    from exopy.testing.measurement.contributions import Flags


pytest_plugins = str('exopy.testing.measurement.workspace.fixtures'),


@pytest.yield_fixture
def workspace(exopy_qtbot, measurement_workbench, measure):
    """Create a measure workspace.

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


def test_workspace_lifecycle(exopy_qtbot, workspace, tmpdir):
    """Test the workspace life cycle.

    """
    workbench = workspace.plugin.workbench
    log = workbench.get_plugin('exopy.app.logging')

    # Check UI creation
    def assert_ui():
        assert workspace._selection_tracker._thread
        assert workspace.last_selected_measure
        assert workspace.content
        assert workspace.dock_area
        assert workbench.get_manifest('exopy.measurement.workspace.menus')
    exopy_qtbot.wait_until(assert_ui)

    # Check log handling
    assert 'exopy.measurement.workspace' in log.handler_ids

    # Check engine handling
    engine = workbench.get_manifest('test.measurement').find('dummy_engine')
    assert engine.workspace_contributing

    # Check measurement creation
    assert len(workspace.plugin.edited_measurements.measurements) == 1
    assert workspace.plugin.edited_measurements.measurements[0].monitors

    # Create a new measure and enqueue it
    workspace.new_measure()

    def assert_measure_created():
        assert len(workspace.plugin.edited_measures.measures) == 2
    exopy_qtbot.wait_until(assert_measure_created)
    m = workspace.plugin.edited_measures.measures[1]
    m.root_task.default_path = str(tmpdir)

    assert workspace.enqueue_measure(m)
    exopy_qtbot.wait(10)

    # Create a tool edition window
    for d in workspace.dock_area.dock_items():
        if d.name == 'meas_0':
            edition_view = d
    ed = edition_view.dock_widget().widgets()[0]
    btn = ed.widgets()[4]
    btn.clicked = True
    exopy_qtbot.wait(10)

    # Check observance of engine selection.
    workspace.plugin.selected_engine = ''
    assert not engine.workspace_contributing
    workspace.plugin.selected_engine = 'dummy'

    def assert_contrib():
        assert engine.workspace_contributing
    exopy_qtbot.wait_until(assert_contrib)

    # Test stopping the workspace
    core = workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})

    assert workspace.plugin.workspace is None
    assert not engine.workspace_contributing
    assert workbench.get_manifest('exopy.measurement.workspace.menus') is None
    assert 'exopy.measurement.workspace' not in log.handler_ids
    assert not workspace._selection_tracker._thread.is_alive()

    # Test restarting now that we have two edited measurement.
    cmd = 'enaml.workbench.ui.select_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})
    assert len(workspace.plugin.edited_measurements.measurements) == 2

    # Check that all dock items have been restored.
    names = [d.name for d in workspace.dock_area.dock_items()]
    for n in ('meas_0', 'meas_1', 'meas_0_tools'):
        assert n in names

    # Create a false monitors_window
    workspace.plugin.processor.monitors_window = Window()
    workspace.plugin.processor.monitors_window.show()
    exopy_qtbot.wait(10)

    # Stop again
    core = workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})

    def assert_not_visible():
        assert not workspace.plugin.processor.monitors_window.visible
    exopy_qtbot.wait_until(assert_not_visible)


@pytest.mark.qt_no_exception_capture
def test_handling_missing_measurement_in_state(exopy_qtbot, workspace):
    """Check the exception raised for a corrupted workspace state.

    """
    workbench = workspace.plugin.workbench

    # Check UI creation
    def assert_ui():
        assert workspace._selection_tracker._thread
        assert workspace.last_selected_measure
        assert workspace.content
        assert workspace.dock_area
        assert workbench.get_manifest('exopy.measurement.workspace.menus')
    exopy_qtbot.wait_until(assert_ui)

    # Test stopping the workspace
    core = workbench.get_plugin('enaml.workbench.core')
    cmd = 'enaml.workbench.ui.close_workspace'
    core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})

    workspace.plugin._workspace_state['measurement_panels'] = {}

    with pytest.raises(RuntimeError):
        cmd = 'enaml.workbench.ui.select_workspace'
        core.invoke_command(cmd, {'workspace': 'exopy.measurement.workspace'})


@pytest.mark.timeout(30)
def test_creating_saving_loading_measure(exopy_qtbot, workspace, monkeypatch,
                                         tmpdir):
    """Test creating, saving, loading a measurement.

    """
    workbench = workspace.plugin.workbench

    # Check UI creation
    def assert_ui():
        assert workspace._selection_tracker._thread
        assert workspace.last_selected_measure
        assert workspace.content
        assert workspace.dock_area
        assert workbench.get_manifest('exopy.measurement.workspace.menus')
    exopy_qtbot.wait_until(assert_ui)

    from exopy.measurement.measurement import Measurement
    from exopy.tasks.api import RootTask

    measurement_tracker = ObjectTracker(Measurement, False)
    root_tracker = ObjectTracker(RootTask, False)
    try:
        assert len(measurement_tracker.alive_instances) == 0
        assert len(root_tracker.alive_instances) == 0

        workspace.new_measurement()
        measurement = workspace.plugin.edited_measurements.measurements[-1]
        assert len(workspace.plugin.edited_measurements.measurements) == 2
        assert measurement.monitors
        assert len(measurement_tracker.alive_instances) == 1
        assert len(root_tracker.alive_instances) == 1

        d = tmpdir.mkdir('measurement_save')
        f = d.join('test')
        from exopy.measurement.workspace.workspace import FileDialogEx

        # Test handling an empty answer.
        @classmethod
        def get(*args, **kwargs):
            pass
        monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
        workspace.save_measurement(measurement)

        assert not d.listdir()

        # Test saving.
        @classmethod
        def get(*args, **kwargs):
            return str(f)
        monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
        workspace.save_measure(measure)
        exopy_qtbot.wait(100)

        f += '.meas.ini'
        assert f in d.listdir()
        f.remove()

        # Test saving on previously used file.
        workspace.save_measurement(measurement)
        assert f in d.listdir()

        f = d.join('test2.meas.ini')

        # Test saving as in a new file.
        @classmethod
        def get(*args, **kwargs):
            return str(f)
        monkeypatch.setattr(FileDialogEx, 'get_save_file_name', get)
        workspace.save_measurement(measurement, False)

        assert f in d.listdir()

        # Test handling error in saving.
        def r(s, m):
            raise Exception()

        monkeypatch.setattr(measurement_tracker.cls, 'save', r)
        with handle_dialog(exopy_qtbot):
            workspace.save_measure(measure)

        # Test loading and dialog reject.
        @classmethod
        def get(*args, **kwargs):
            pass
        monkeypatch.setattr(FileDialogEx, 'get_open_file_name', get)
        assert workspace.load_measurement('file') is None

        # Test loading measurement.
        @classmethod
        def get(*args, **kwargs):
            return str(f)
        monkeypatch.setattr(FileDialogEx, 'get_open_file_name', get)
        workspace.load_measurement('file')

        assert len(workspace.plugin.edited_measurements.measurements) == 3
        m = workspace.plugin.edited_measurements.measurements[2]
        assert m.path == str(f)
        assert workspace._get_last_selected_measurement() is m

        # Test loading a measurement in an existing dock_item and check the old
        # one does not remain in the list of edited measurements
        panel = workspace.dock_area.find('meas_0')
        panel.measurement.name = '__dummy__'
        old_measurement = panel.measurement
        workspace.load_measurement('file', panel)
        assert panel.measurement.name != '__dummy__'
        assert (old_measurement not in
                workspace.plugin.edited_measurements.measurements)
        del old_measurement

        # Test handling loading error.
        @classmethod
        def r(cls, measurement_plugin, path, build_dep=None):
            return None, {'r': 't'}

        monkeypatch.setattr(Measure, 'load', r)
        with handle_dialog(exopy_qtbot, handler=lambda bot, d: d.maximize()):
            workspace.load_measure('file')

        with pytest.raises(NotImplementedError):
            workspace.load_measurement('template')

        # Check that have only two measurements and root (no leakage)
        # HINT : use for debugging
    #    from pprint import pprint
    #    print(workspace.plugin.edited_measurements.measurements)
    #    pprint(measurement_tracker.list_referrers())
        assert len(measurement_tracker.alive_instances) == 3
        assert len(root_tracker.alive_instances) == 3

    finally:
        measurement_tracker.stop_tracking()
        root_tracker.stop_tracking()


def test_handling_all_tools_combinations(workspace):
    """Test creating all kind of tools as defaults, and handling errors for
    all.

    """
    plugin = workspace.plugin
    plugin.default_pre_hooks = ['dummy', 'none']
    plugin.default_monitors = ['dummy', 'none']
    plugin.default_post_hooks = ['dummy', 'none']

    workspace.new_measurement()
    m = workspace.plugin.edited_measurements.measurements[-1]
    assert len(m.pre_hooks) == 2
    assert len(m.monitors) == 1
    assert len(m.post_hooks) == 1


def assert_dependencies_released(workspace, measurement):
    """Make sure that after an enqueueing attempt all dependencies are
    released and all cache are clean.

    """
    # Make sure runtimes are always released.
    runtim_holder = workspace.plugin.workbench.get_manifest('test.measurement')
    assert not runtim_holder.find('runtime_dummy1').collected
    assert not runtim_holder.find('runtime_dummy2').collected

    # Check build depepndencies have been cleaned so that they are not re-used
    for c in ('_build_analysis', '_build_dependencies', '_runtime_analysis',
              '_runtime_dependencies', '_runtime_map'):
        assert not getattr(measurement.dependencies, c)


@pytest.mark.timeout(10)
def test_enqueueing_and_reenqueueing_measurement(workspace, monkeypatch,
                                                 tmpdir):
    """Test enqueue a measurement and re-enqueue it.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    m.root_task.default_path = str(tmpdir)
    from exopy.measurement.workspace.workspace import os
    m.add_tool('pre-hook', 'dummy')
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)

    def r(f):
        raise OSError()

    # Fail remove temp file. Seen in coverage.
    monkeypatch.setattr(os, 'remove', r)
    old_path = m.path

    assert workspace.enqueue_measurement(m)

    # Make sure we do not alter the saving path
    assert m.path == old_path

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)

    # Check enqueued, status
    assert workspace.plugin.enqueued_measurements.measurements
    m2 = workspace.plugin.enqueued_measurements.measurements[0]
    assert m2.status == 'READY'

    # Test re-enqueuing
    m2.status = 'COMPLETED'
    from exopy.measurement.measurement import Measurement

    def e(m):
        m.name = 'R'
    monkeypatch.setattr(Measurement, 'enter_edition_state', e)
    workspace.reenqueue_measurement(m2)
    assert m2.name == 'R'
    assert m2.status == 'READY'


@pytest.mark.timeout(10)
def test_enqueueing_fail_runtime(workspace, monkeypatch, exopy_qtbot):
    """Test enqueueing a measure for which runtimes cannot be collected.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    m.add_tool('pre-hook', 'dummy')
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', True)
    with handle_dialog(exopy_qtbot):
        workspace.enqueue_measure(m)

    assert not workspace.plugin.enqueued_measurements.measurements

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)

    w = workspace.plugin.workbench
    d = w.get_manifest('test.measurement')
    assert d.find('runtime_dummy2').called


@pytest.mark.timeout(10)
def test_enqueueing_fail_checks(workspace, exopy_qtbot):
    """Test enqueueing a measure not passing the checks.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    with handle_dialog(exopy_qtbot, 'reject'):
        workspace.enqueue_measure(m)

    assert not workspace.plugin.enqueued_measurements.measurements

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)


@pytest.mark.timeout(10)
def test_enqueueing_abort_warning(workspace, monkeypatch, tmpdir, exopy_qtbot):
    """Test aborting enqueueing because some checks raised warnings.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    m.root_task.default_path = str(tmpdir)
    from exopy.measurement.measurement import Measurement

    witness = []

    def check(*args, **kwargs):
        witness.append(None)
        return True, {'r': {'t': 's'}}
    monkeypatch.setattr(Measurement, 'run_checks', check)

    with handle_dialog(exopy_qtbot, 'reject'):
        workspace.enqueue_measure(m)

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)

    assert not workspace.plugin.enqueued_measurements.measurements

    assert witness


@pytest.mark.timeout(10)
def test_enqueueing_after_warning(workspace, monkeypatch, tmpdir, exopy_qtbot):
    """Test enqueueing after some checks raised warnings.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    m.root_task.default_path = str(tmpdir)
    from exopy.measurement.measurement import Measurement

    witness = []

    def check(*args, **kwargs):
        witness.append(None)
        return True, {'r': {'t': 's'}}
    monkeypatch.setattr(Measurement, 'run_checks', check)

    with handle_dialog(exopy_qtbot):
        assert workspace.enqueue_measure(m)

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)

    assert witness


@pytest.mark.timeout(10)
def test_force_enqueueing(exopy_qtbot, workspace):
    """Test enqueueing a measure not passing the checks.

    """
    m = workspace.plugin.edited_measurements.measurements[0]

    def handle_error_report(bot, dial):

        def answer_question(bot, dial):
            dial.buttons[0].was_clicked = True

        with handle_dialog(bot, 'accept', answer_question,
                           cls=MessageBox):
            dial.central_widget().widgets()[-1].clicked = True

    with handle_dialog(exopy_qtbot, handler=handle_error_report,
                       skip_answer=True):
        workspace.enqueue_measure(m)

    assert workspace.plugin.enqueued_measurements.measurements

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)


@pytest.mark.timeout(10)
def test_force_enqueueing_abort(exopy_qtbot, workspace):
    """Test enqueueing a measure not passing the checks, but aborting.

    """
    m = workspace.plugin.edited_measurements.measurements[0]

    def handle_error_report(bot, dial):
        def answer_question(bot, dial):
            dial.buttons[1].was_clicked = True

        with handle_dialog(bot, 'reject', answer_question,
                           cls=MessageBox):
            dial.central_widget().widgets()[-1].clicked = True

    with handle_dialog(exopy_qtbot, handler=handle_error_report,
                       skip_answer=True):
        workspace.enqueue_measure(m)

    assert not workspace.plugin.enqueued_measurements.measurements

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)


@pytest.mark.timeout(10)
def test_enqueuing_fail_reload(workspace, monkeypatch, tmpdir, exopy_qtbot):
    """Test failing when reloading the measure after saving.

    """
    m = workspace.plugin.edited_measurements.measurements[0]
    m.root_task.default_path = str(tmpdir)
    from exopy.measurement.measurement import Measurement

    witness = []

    @classmethod
    def r(cls, measurement_plugin, path, build_dep=None):
        witness.append(None)
        return None, {'r': 't'}
    monkeypatch.setattr(Measurement, 'load', r)

    with handle_dialog(exopy_qtbot):
        workspace.enqueue_measure(m)

    # Check dependencies are cleaned up
    assert_dependencies_released(workspace, m)

    assert not workspace.plugin.enqueued_measurements.measurements

    assert witness


@pytest.mark.timeout(10)
def test_measurement_execution(workspace, exopy_qtbot):
    """Test selecting a new engine if no engine is selected and that commands
    are piped to the processor.

    """
    from exopy.measurement.processor import MeasurementProcessor
    from atom.api import Unicode, Dict

    class P(MeasurementProcessor):

        called = Unicode()

        args = Dict()

        def start_measurement(self, measurement):
            self.called = 'start'

        def pause_measurement(self):
            self.called = 'pause'

        def resume_measurement(self):
            self.called = 'resume'

        def stop_measurement(self, no_post_exec=False, force=False):
            self.args = dict(no_post_exec=no_post_exec,
                             force=force)
            self.called = 'stop'

        def stop_processing(self, no_post_exec=False, force=False):
            self.args = dict(no_post_exec=no_post_exec,
                             force=force)
            self.called = 'processing'

    workspace.plugin.processor = P()
    workspace.plugin.selected_engine = ''
    workspace.plugin.processor.continuous_processing = False

    # Test not selecting an engine.
    with handle_dialog(exopy_qtbot, 'reject'):
        workspace.start_processing_measurements()

    # Test not selecting an engine.
    with handle_dialog(exopy_qtbot, 'reject'):
        workspace.process_single_measure(None)

    workspace.plugin.enqueued_measurements.measurements.append(
        workspace.plugin.edited_measurements.measurements[0])

    def set_eng(bot, dialog):
        dialog.selected_decl = workspace.plugin._engines.contributions['dummy']

    with handle_dialog(exopy_qtbot, 'accept', set_eng):
        workspace.start_processing_measurements()

    assert workspace.plugin.processor.continuous_processing
    assert workspace.plugin.processor.called == 'start'

    workspace.plugin.enqueued_measurements.measurements = []
    with handle_dialog(exopy_qtbot):
        workspace.start_processing_measurements()

    workspace.plugin.processor.called = ''
    workspace.process_single_measurement(None)
    assert not workspace.plugin.processor.continuous_processing
    assert workspace.plugin.processor.called == 'start'

    workspace.pause_current_measurement()
    assert workspace.plugin.processor.called == 'pause'

    workspace.resume_current_measurement()
    assert workspace.plugin.processor.called == 'resume'

    workspace.stop_current_measurement(no_post_exec=True)
    assert workspace.plugin.processor.called == 'stop'
    assert workspace.plugin.processor.args == dict(no_post_exec=True,
                                                   force=False)

    workspace.stop_processing_measurements(force=True)
    assert workspace.plugin.processor.called == 'processing'
    assert workspace.plugin.processor.args == dict(no_post_exec=False,
                                                   force=True)


def test_remove_processed_measurements(workspace):
    """Test removing already processed measurements from enqueued ones.

    """
    states = ('SKIPPED', 'FAILED', 'COMPLETED', 'INTERRUPTED', 'READY',
              'RUNNING', 'PAUSING', 'PAUSED', 'RESUMING',
              'STOPPING', 'EDITING')

    for i, s in enumerate(states):
        workspace.new_measurement()
        m = workspace.plugin.edited_measurements.measurements[-1]
        workspace.plugin.enqueued_measurements.measurements.append(m)
        m.status = s

    workspace.remove_processed_measurements()

    for m in workspace.plugin.enqueued_measurements.measurements:
        assert m.status not in ('SKIPPED', 'FAILED', 'COMPLETED',
                                'INTERRUPTED')


def test_creating_measurement_when_low_index_was_destroyed(workspace):
    """Test that adding an edited measurement when a previous one panel was closed
    re-use the index.

    """
    workspace.new_measurement()
    workspace.dock_area.find('meas_0').destroy()
    workspace.new_measurement()  # Create a dock item for a missing index
    m = workspace.plugin.edited_measurements.measurements[-1]
    dock = [d for d in workspace.dock_area.dock_items()
            if getattr(d, 'measurement', None) is m][0]
    assert dock.name == 'meas_0'
