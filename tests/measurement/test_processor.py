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
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml
import pytest
from future.builtins import str
from threading import Thread

from exopy.measurement.measurement import Measurement
from exopy.tasks.api import RootTask

from exopy.testing.util import ErrorDialogException, process_app_events

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
def processor(windows, measurement_workbench, measurement):
    """Fixture starting the measurement plugin and returning the processor.

    Use app because we need run the event loop

    """
    # measurement ensures that contributions are there
    measurement_workbench.register(UIManifest())
    measurement_workbench.register(TasksManagerManifest())
    plugin = measurement_workbench.get_plugin('exopy.measurement')
    plugin.selected_engine = 'dummy'

    return plugin.processor


def process_and_assert(test_func, args=(), kwargs={}, time=0.01, count=1000):
    """Process events and check test_func value.

    """
    process_app_events()
    counter = 0
    while not test_func(*args, **kwargs):
        sleep(time)
        process_app_events()
        if counter > count:
            assert False
        counter += 1
    process_app_events()


def process_and_join_thread(thread, timeout=0.1):
    """Process application events and join a thread.

    """
    def test_func():
        thread.join(timeout)
        return not thread.is_alive()

    process_and_assert(test_func)


def wait_and_process(waiting_function):
    """Call a function which can timeout and process app events.

    """
    i = 0
    while not waiting_function(timeout=0.04):
        process_app_events()
        i += 1
        if i > 10000:
            assert False
    process_app_events()


def test_setting_continuous_processing(processor):
    """Test that the post-setter does update the flag.

    """
    processor.continuous_processing = False
    assert not processor._state.test('continuous_processing')
    processor.continuous_processing = True
    assert processor._state.test('continuous_processing')


@pytest.mark.timeout(10)
def test_starting_measurement_no_measurement_enqueued(processor):
    """Test starting next measurement in the queue when no measures are enqueued.

    """
    processor.start_measurement(None)
    process_and_join_thread(processor._thread)
    assert not processor.active


def test_starting_measurement_thread_not_dying(processor, measurement):
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
    sleep(0.1)
    process_app_events()
    with pytest.raises(ErrorDialogException):
        core.invoke_command('exopy.app.errors.exit_error_gathering')


@pytest.mark.timeout(60)
def test_running_full_measurement(app, processor, measurement_with_tools,
                                  windows, dialog_sleep, tmpdir):
    """Test running a complete measurement with pre/post-hooks and monitor.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.continuous_processing = False
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    assert measurement is processor.running_measurement
    assert measurement.status == 'RUNNING'
    assert tmpdir.listdir()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    assert processor.monitors_window
    assert processor.monitors_window.measurement is measurement
    assert measurement.monitors['dummy'].running
    sleep(dialog_sleep)
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    assert measurement.task_execution_result
    assert not measurement.monitors['dummy'].running
    assert measurement.monitors['dummy'].received_news

    post_hook.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(60)
def test_running_measurement_whose_runtime_are_unavailable(
        processor, monkeypatch, measurement_with_tools):
    """Test running whose runtime dependencies are unavailable.

    """
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    process_and_join_thread(processor._thread)
    assert measurement_with_tools.status == 'SKIPPED'


@pytest.mark.timeout(60)
def test_running_measurement_failing_checks(processor, measurement_with_tools):
    """Test running a measurement failing to pass the tests.

    """
    measurement_with_tools.pre_hooks['dummy'].fail_check = True
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    process_and_join_thread(processor._thread)
    assert measurement_with_tools.status == 'FAILED'
    assert 'checks' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_pre_hooks(processor,
                                               measurement_with_tools):
    """Test running a measurement whose pre-hooks fail to execute.

    """
    measurement_with_tools.pre_hooks['dummy'].fail_run = True
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement_with_tools.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()
    pre_hook.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement_with_tools.status == 'FAILED'
    assert 'pre-execution' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_main_task(processor,
                                               measurement_with_tools):
    """Test running a measurement whose pre-hooks fail to execute.

    """
    measurement = measurement_with_tools
    processor.engine = processor.plugin.create('engine', 'dummy')
    processor.engine.fail_perform = True
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()
    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    process_and_join_thread(processor._thread)

    assert measurement.status == 'FAILED'
    assert 'main task' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_measurement_failing_post_hooks(processor,
                                                measurement_with_tools):
    """Test running a measurement whose post-hooks fail to execute.

    """
    measurement = measurement_with_tools
    measurement_with_tools.post_hooks['dummy'].fail_run = True
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    process_and_join_thread(processor._thread)

    assert measurement_with_tools.status == 'FAILED'
    assert 'post-execution' in measurement_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_running_forced_enqueued_measurement(processor,
                                             measurement_with_tools):
    """Test running a measurement about which we know that checks are failing.

    """
    measurement = measurement_with_tools
    measurement.forced_enqueued = True
    measurement.pre_hooks['dummy'].fail_check = True
    processor.start_measurement(measurement_with_tools)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)
    assert processor.engine.measurement_force_enqueued
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    process_and_join_thread(processor._thread)


@pytest.mark.parametrize('mode', ['between hooks', 'after hooks'])
@pytest.mark.timeout(60)
def test_stopping_measurement_while_preprocessing(mode, processor,
                                                  measurement_with_tools):
    """Test asking the processor to stop while is is running the pre-hooks.

    The post-hooks should not be run.

    """
    measurement = measurement_with_tools
    if mode == 'between hooks':
        # Will see the difference only in coverage
        measurement.move_tool('pre-hook', 0, 1)
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()
    processor.stop_measurement(no_post_exec=True)
    assert pre_hook.stop_called

    pre_hook.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_measurement_while_running_main(processor,
                                                 measurement_with_tools):
    """Test asking the processor to stop while is is running the main task.

    The post-hooks should be run.

    """
    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.stop_measurement()
    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_measurement_while_postprocessing(processor,
                                                   measurement_with_tools):
    """Test asking the processor to stop while is is running the post hooks.

    """
    measurement = measurement_with_tools
    measurement.add_tool('post-hook', 'dummy2')
    measurement.post_hooks['dummy2'].fail_run = True
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    processor.stop_measurement(force=True)
    assert post_hook.stop_called
    post_hook.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(60)
def test_stopping_processing(processor, measurement_with_tools):
    """Test stopping processing while running the main task..

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.stop_processing(no_post_exec=True)
    processor.engine.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(60)
def test_stopping_processing_in_hook(processor, measurement_with_tools):
    """Test stopping processing while running a hook.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    processor.stop_processing(no_post_exec=True)
    pre_hook.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(240)
def test_stopping_processing_while_in_pause(processor, measurement_with_tools):
    """Test stopping processing while in pause before starting main.

    """
    plugin = processor.plugin.workbench.get_plugin('exopy.measurement')
    measure2 = Measurement(plugin=plugin, root_task=RootTask(),
                           name='Dummy', id='002')
    processor.plugin.enqueued_measurements.add(measure2)

    def wait_on_state_paused(timeout):
        return processor._state.wait(timeout, 'paused')

    measurement = measurement_with_tools
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    pre_hook = measurement.pre_hooks['dummy']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    processor.pause_measurement()
    pre_hook.accept_pause = False
    pre_hook.go_on.set()

    wait_and_process(wait_on_state_paused)

    processor.stop_processing(no_post_exec=True)
    sleep(0.2)

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measurement.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(480)
def test_pausing_measurement(processor, measurement_with_tools):
    """Test running a complete measurement with pre/post-hooks and monitor.

    """
    measurement = measurement_with_tools
    measurement.add_tool('pre-hook', 'dummy2')
    measurement.move_tool('pre-hook', 2, 0)
    measurement.add_tool('post-hook', 'dummy2')
    processor.start_measurement(measurement)

    process_and_assert(getattr, (processor, 'active'))

    def wait_on_state_paused(timeout):
        return processor._state.wait(timeout, 'paused')

    pre_hook = measurement.pre_hooks['dummy2']
    process_and_assert(pre_hook.waiting.wait, (5,))
    process_app_events()

    # Pause inside a pre_hook.
    processor.pause_measurement()
    process_app_events()
    assert measurement.status == 'PAUSING'
    pre_hook.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measurement.status == 'PAUSED'

    processor.resume_measurement()
    wait_and_process(pre_hook.signal_resuming.wait)
    assert measurement.status == 'RESUMING'
    pre_hook.go_on_resuming.set()
    wait_and_process(pre_hook.signal_resumed.wait)
    assert measurement.status == 'RUNNING'

    # Pause in between two pre_hooks
    processor.pause_measurement()
    pre_hook.go_on_resumed.set()
    wait_and_process(wait_on_state_paused)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()

    # Pause just before starting the main measurement.
    pre_hook2 = measurement.pre_hooks['dummy']
    pre_hook2.accept_pause = False
    wait_and_process(pre_hook2.waiting.wait)
    assert measurement.status == 'RUNNING'
    processor.pause_measurement()
    pre_hook2.go_on.set()
    wait_and_process(wait_on_state_paused)
    processor.resume_measurement()

    # Pause during the main task execution.
    wait_and_process(processor.engine.waiting.wait)
    processor.pause_measurement()
    processor.engine.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()
    wait_and_process(processor.engine.signal_resuming.wait)
    assert measurement.status == 'RESUMING'
    processor.engine.go_on_resuming.set()
    wait_and_process(processor.engine.signal_resumed.wait)
    assert measurement.status == 'RUNNING'
    processor.engine.go_on_resumed.set()

    # Pause inside a post_hook.
    post_hook = measurement.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)
    processor.pause_measurement()
    process_app_events()
    assert measurement.status == 'PAUSING'
    post_hook.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measurement.status == 'PAUSED'

    processor.resume_measurement()
    wait_and_process(post_hook.signal_resuming.wait)
    assert measurement.status == 'RESUMING'
    post_hook.go_on_resuming.set()
    wait_and_process(post_hook.signal_resumed.wait)
    assert measurement.status == 'RUNNING'

    # Pause in between two post_hooks
    processor.pause_measurement()
    post_hook.go_on_resumed.set()
    wait_and_process(wait_on_state_paused)
    assert measurement.status == 'PAUSED'
    processor.resume_measurement()

    post_hook2 = measurement.post_hooks['dummy2']
    wait_and_process(post_hook2.waiting.wait)
    post_hook2.go_on.set()

    process_and_join_thread(processor._thread)
    assert measurement.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measurement')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


def test_monitor_creation(processor, measurement, dialog_sleep):
    """Test all possible possibilities when creating a monitor dock item.

    """
    def run(measurement):
        t = Thread(target=processor._start_monitors, args=(measurement,))
        t.start()
        while t.is_alive():
            process_app_events()
            sleep(0.001)
        process_app_events()
        sleep(dialog_sleep)

    processor.engine = processor.plugin.create('engine', 'dummy')

    measurement.add_tool('monitor', 'dummy')
    run(measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measurement.add_tool('monitor', 'dummy2')
    run(measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measurement.remove_tool('monitor', 'dummy2')
    run(measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measurement.add_tool('monitor', 'dummy3')
    run(measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measurement.add_tool('monitor', 'dummy4')
    run(measurement)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    processor.plugin.stop()
    assert not processor.monitors_window
