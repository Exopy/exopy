# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the working of the measurement processor.

"""
import enaml
import pytest
from threading import Thread

from exopy.measurement.measurement import Measurement
from exopy.tasks.api import RootTask

from exopy.testing.util import ErrorDialogException

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest

    from exopy.tasks.manifest import TasksManagerManifest
    from exopy.testing.measurement.contributions import Flags


@pytest.fixture
def measurement_with_tools(measurement, tmpdir):
    """Create a measurement with all dummy tools attached.

    """
    measurement.add_tool('pre-hook', 'dummy')
    measurement.add_tool('post-hook', 'dummy')
    measurement.add_tool('monitor', 'dummy')
    measurement.root_task.default_path = str(tmpdir)
    return measurement


@pytest.fixture
def processor(exopy_qtbot, measurement_workbench, measurement):
    """Fixture starting the measurement plugin and returning the processor.

    Use app because we need run the event loop

    """
    # measurement ensures that contributions are there
    measurement_workbench.register(UIManifest())
    measurement_workbench.register(TasksManagerManifest())
    plugin = measurement_workbench.get_plugin('exopy.measurement')
    plugin.selected_engine = 'dummy'

    return plugin.processor


def process_and_join_thread(bot, thread, timeout=0.1):
    """Process application events and join a thread.

    """
    def test_func():
        thread.join(timeout)
        assert not thread.is_alive()

    bot.wait_until(test_func, 20e3)


def test_setting_continuous_processing(processor):
    """Test that the post-setter does update the flag.

    """
    processor.continuous_processing = False
    assert not processor._state.test('continuous_processing')
    processor.continuous_processing = True
    assert processor._state.test('continuous_processing')


@pytest.mark.timeout(10)
def test_starting_measurement_no_measurement_enqueued(exopy_qtbot, processor):
    """Test starting next measurement in the queue when no measurements are
    enqueued.

    """
    processor.start_measurement(None)
    process_and_join_thread(exopy_qtbot, processor._thread)

    def assert_inactive():
        assert not processor.active
    exopy_qtbot.wait_until(assert_inactive)


def test_starting_measurement_thread_not_dying(exopy_qtbot, processor,
                                               measurement):
    """Test starting but failing to stop the backgground thread.

    """
    class FalseThread(object):

        def __init__(self, processor):
            self.state = processor._state

        def is_alive(self):
            return True

        def join(self, timeout):
            if not self.state.test('stop_processing'):
                raise Exception()

    processor._thread = FalseThread(processor)
    core = processor.plugin.workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('exopy.app.errors.enter_error_gathering')
    processor.start_measurement(None)
    exopy_qtbot.wait(100)
    with pytest.raises(ErrorDialogException):
        core.invoke_command('exopy.app.errors.exit_error_gathering')


@pytest.mark.timeout(60)
def test_running_full_measurement(exopy_qtbot, processor, measurement_with_tools,
                              dialog_sleep, tmpdir):
    """Test running a complete measurement with pre/post-hooks and monitor.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.continuous_processing = False
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)
    assert measurement is processor.running_measurement
    assert measurement.status == 'RUNNING'
    assert tmpdir.listdir()

    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    assert processor.monitors_window
    assert processor.monitors_window.measurement is measurement
    assert measurement.monitors['dummy'].running
    exopy_qtbot.wait(dialog_sleep)
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    assert measurement.task_execution_result
    assert not measurement.monitors['dummy'].running
    assert measurement.monitors['dummy'].received_news

    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(60)
def test_running_measurement_whose_runtime_are_unavailable(
        processor, monkeypatch, measurement_with_tools, exopy_qtbot):
    """Test running whose runtime dependencies are unavailable.

    """
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement_with_tools.status == 'SKIPPED'


@pytest.mark.timeout(60)
def test_running_measurement_failing_checks(exopy_qtbot, processor,
                                            measurement_with_tools):
    """Test running a measurement failing to pass the tests.

    """
    measurement_with_tools.pre_hooks['dummy'].fail_check = True
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement_with_tools.status == 'FAILED'
    assert 'checks' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_pre_hooks(exopy_qtbot, processor,
                                               measurement_with_tools):
    """Test running a measurement whose pre-hooks fail to execute.

    """
    measurement_with_tools.pre_hooks['dummy'].fail_run = True
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement_with_tools.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)
    exopy_qtbot.wait(10)
    pre_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement_with_tools.status == 'FAILED'
    assert 'pre-execution' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_main_task(exopy_qtbot, processor,
                                               measurement_with_tools):
    """Test running a measurement whose pre-hooks fail to execute.

    """
    measurement = measurement_with_tools
    processor.engine = processor.plugin.create('engine', 'dummy')
    processor.engine.fail_perform = True
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)
    exopy_qtbot.wait(10)
    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)

    assert measurement.status == 'FAILED'
    assert 'main task' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_post_hooks(exopy_qtbot, processor,
                                                measurement_with_tools):
    """Test running a measurement whose post-hooks fail to execute.

    """
    measurement = measurement_with_tools
    measurement_with_tools.post_hooks['dummy'].fail_run = True
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    pre_hook.go_on.set()
    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    processor.engine.go_on.set()
    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)

    assert measurement_with_tools.status == 'FAILED'
    assert 'post-execution' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_forced_enqueued_measurement(exopy_qtbot, processor,
                                         measurement_with_tools):
    """Test running a measurement about which we know that checks are failing.

    """
    measurement = measurement_with_tools
    measurement.forced_enqueued = True
    measurement.pre_hooks['dummy'].fail_check = True
    processor.start_measurement(measurement_with_tools)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)
    assert processor.engine.measurement_force_enqueued
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)


@pytest.mark.parametrize('mode', ['between hooks', 'after hooks'])
@pytest.mark.timeout(60)
def test_stopping_measurement_while_preprocessing(exopy_qtbot, mode, processor,
                                                  measurement_with_tools):
    """Test asking the processor to stop while is is running the pre-hooks.

    The post-hooks should not be run.

    """
    measurement = measurement_with_tools
    if mode == 'between hooks':
        # Will see the difference only in coverage
        measurement.move_tool('pre-hook', 0, 1)
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)
    processor.stop_measurement(no_post_exec=True)
    assert pre_hook.stop_called

    pre_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_measurement_while_running_main(exopy_qtbot, processor,
                                                 measurement_with_tools):
    """Test asking the processor to stop while is is running the main task.

    The post-hooks should be run.

    """
    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    processor.stop_measurement()
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_measurement_while_postprocessing(exopy_qtbot, processor,
                                                   measurement_with_tools):
    """Test asking the processor to stop while is is running the post hooks.

    """
    measurement = measurement_with_tools
    measurement.add_tool('post-hook', 'dummy2')
    measurement.post_hooks['dummy2'].fail_run = True
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04),
                           timeout=40e3)

    processor.stop_measurement(force=True)
    assert post_hook.stop_called
    post_hook.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_processing(exopy_qtbot, processor, measurement_with_tools):
    """Test stopping processing while running the main task..

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)

    processor.stop_processing(no_post_exec=True)
    processor.engine.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        assert not processor._thread.is_alive()

    exopy_qtbot.wait_until(lambda: wait(0.04), timeout=40e3)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(60)
def test_stopping_processing_in_hook(exopy_qtbot, processor,
                                     measurement_with_tools):
    """Test stopping processing while running a hook.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    processor.stop_processing(no_post_exec=True)
    pre_hook.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        assert not processor._thread.is_alive()

    exopy_qtbot.wait_until(lambda: wait(0.04), timeout=40e3)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(240)
def test_stopping_processing_while_in_pause(exopy_qtbot, processor,
                                            measurement_with_tools):
    """Test stopping processing while in pause before starting main.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    def wait_on_state_paused(timeout):
        assert processor._state.wait(timeout, 'paused')

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    pre_hook = measurement.pre_hooks['dummy']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    processor.pause_measurement()
    pre_hook.accept_pause = False
    pre_hook.go_on.set()

    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)

    processor.stop_processing(no_post_exec=True)
    exopy_qtbot.wait(0.2)

    def wait(timeout):
        processor._thread.join(timeout)
        assert not processor._thread.is_alive()

    exopy_qtbot.wait_until(lambda: wait(0.04), timeout=40e3)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(480)
def test_pausing_measurement(exopy_qtbot, processor, measurement_with_tools):
    """Test running a complete measurement with pre/post-hooks and monitor.

    """
    measurement = measurement_with_tools
    measurement.add_tool('pre-hook', 'dummy2')
    measurement.move_tool('pre-hook', 2, 0)
    measurement.add_tool('post-hook', 'dummy2')
    processor.start_measurement(measurement)

    def assert_active():
        assert processor.active
    exopy_qtbot.wait_until(assert_active)

    def wait_on_state_paused(timeout):
        assert processor._state.wait(timeout, 'paused')

    pre_hook = measurement.pre_hooks['dummy2']

    def assert_wait():
        assert pre_hook.waiting.wait(5)
    exopy_qtbot.wait_until(assert_wait, timeout=50e3)

    # Pause inside a pre_hook.
    processor.pause_measurement()
    exopy_qtbot.wait_until(lambda: measurement.status == 'PAUSING')
    pre_hook.go_on.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    assert measurement.status == 'PAUSED'

    processor.resume_measurement()
    exopy_qtbot.wait_until(lambda: pre_hook.signal_resuming.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RESUMING'
    pre_hook.go_on_resuming.set()
    exopy_qtbot.wait_until(lambda: pre_hook.signal_resumed.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RUNNING'

    # Pause in between two pre_hooks
    processor.pause_measurement()
    pre_hook.go_on_resumed.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()

    # Pause just before starting the main measurement.
    pre_hook2 = measurement.pre_hooks['dummy']
    pre_hook2.accept_pause = False
    exopy_qtbot.wait_until(lambda: pre_hook2.waiting.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RUNNING'
    processor.pause_measurement()
    pre_hook2.go_on.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    processor.resume_measurement()

    # Pause during the main task execution.
    exopy_qtbot.wait_until(lambda: processor.engine.waiting.wait(0.04),
                           timeout=40e3)
    processor.pause_measurement()
    processor.engine.go_on.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()
    exopy_qtbot.wait_until(lambda: processor.engine.signal_resuming.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RESUMING'
    processor.engine.go_on_resuming.set()
    exopy_qtbot.wait_until(lambda: processor.engine.signal_resumed.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RUNNING'
    processor.engine.go_on_resumed.set()

    # Pause inside a post_hook.
    post_hook = measurement.post_hooks['dummy']
    exopy_qtbot.wait_until(lambda: post_hook.waiting.wait(0.04), timeout=40e3)
    processor.pause_measurement()
    exopy_qtbot.wait_until(lambda: measurement.status == 'PAUSING')
    post_hook.go_on.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    assert measurement.status == 'PAUSED'

    processor.resume_measurement()
    exopy_qtbot.wait_until(lambda: post_hook.signal_resuming.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RESUMING'
    post_hook.go_on_resuming.set()
    exopy_qtbot.wait_until(lambda: post_hook.signal_resumed.wait(0.04),
                           timeout=40e3)
    assert measurement.status == 'RUNNING'

    # Pause in between two post_hooks
    processor.pause_measurement()
    post_hook.go_on_resumed.set()
    exopy_qtbot.wait_until(lambda: wait_on_state_paused(0.04), timeout=40e3)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()

    post_hook2 = measurement.post_hooks['dummy2']
    exopy_qtbot.wait_until(lambda: post_hook2.waiting.wait(0.04),
                           timeout=40e3)
    post_hook2.go_on.set()

    process_and_join_thread(exopy_qtbot, processor._thread)
    assert measurement.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


def test_monitor_creation(processor, measurement, exopy_qtbot,  dialog_sleep):
    """Test all possible possibilities when creating a monitor dock item.

    """
    def run(exopy_qtbot, measurement):
        t = Thread(target=processor._start_monitors, args=(measurement,))
        t.start()
        exopy_qtbot.wait_until(lambda: not t.is_alive(), timeout=10e3)
        exopy_qtbot.wait(dialog_sleep)

    processor.engine = processor.plugin.create('engine', 'dummy')

    measurement.add_tool('monitor', 'dummy')
    run(exopy_qtbot, measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measurement.add_tool('monitor', 'dummy2')
    run(exopy_qtbot, measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measurement.remove_tool('monitor', 'dummy2')
    run(exopy_qtbot, measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measurement.add_tool('monitor', 'dummy3')
    run(exopy_qtbot, measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measurement.add_tool('monitor', 'dummy4')
    run(exopy_qtbot, measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    processor.plugin.stop()
    assert not processor.monitors_window
