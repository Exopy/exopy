# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the working of the measure processor.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml
import pytest
from future.builtins import str
from threading import Thread

from ecpy.measure.measure import Measure
from ecpy.tasks.api import RootTask

from ..util import (ErrorDialogException, process_app_events)

with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest

    from ecpy.tasks.manager.manifest import TasksManagerManifest
    from .contributions import Flags


@pytest.fixture
def measure_with_tools(measure, tmpdir):
    """Create a measure with all dummy tools attached.

    """
    measure.add_tool('pre-hook', 'dummy')
    measure.add_tool('post-hook', 'dummy')
    measure.add_tool('monitor', 'dummy')
    measure.root_task.default_path = str(tmpdir)
    return measure


@pytest.fixture
def processor(app, measure_workbench, measure):
    """Fixture starting the measure plugin and returning the processor.

    Use app because we need run the event loop

    """
    # measure ensures that contributions are there
    measure_workbench.register(UIManifest())
    measure_workbench.register(TasksManagerManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')
    plugin.selected_engine = 'dummy'
    return plugin.processor


def wait_and_process(waiting_function):
    """Call a function which can timeout and process app events.

    """
    i = 0
    while not waiting_function(timeout=0.001):
        process_app_events()
        i += 1
        if i > 1000:
            assert False
    process_app_events()


def test_setting_continuous_processing(processor):
    """Test that the post-setter does update the flag.

    """
    processor.continuous_processing = False
    assert not processor._state.test('continuous_processing')
    processor.continuous_processing = True
    assert processor._state.test('continuous_processing')


@pytest.mark.timeout(1)
def test_starting_measure_no_measure_enqueued(processor):
    """Test starting next measure in the queue when no measures are enqueued.

    """
    processor.start_measure(None)
    assert processor.active
    processor._thread.join()
    process_app_events()
    assert not processor.active


def test_starting_measure_thread_not_dying(processor, measure):
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
    core.invoke_command('ecpy.app.errors.enter_error_gathering')
    processor.start_measure(None)
    with pytest.raises(ErrorDialogException):
        core.invoke_command('ecpy.app.errors.exit_error_gathering')


@pytest.mark.timeout(5)
def test_running_full_measure(app, processor, measure_with_tools, windows,
                              dialog_sleep, tmpdir):
    """Test running a complete measure with pre/post-hooks and monitor.

    """
    plugin = processor.plugin.workbench.get_plugin('ecpy.measure')
    measure2 = Measure(plugin=plugin, root_task=RootTask(),
                       name='Dummy', id='002')
    processor.plugin.enqueued_measures.add(measure2)

    measure = measure_with_tools
    processor.continuous_processing = False
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()
    assert measure is processor.running_measure
    assert measure.status == 'RUNNING'
    assert tmpdir.listdir()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    assert processor.monitors_window
    assert processor.monitors_window.measure is measure
    assert measure.monitors['dummy'].running
    sleep(dialog_sleep)
    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    assert measure.task_execution_result
    assert not measure.monitors['dummy'].running
    assert measure.monitors['dummy'].received_news

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(5)
def test_running_measure_whose_runtime_are_unavailable(processor, monkeypatch,
                                                       measure_with_tools):
    """Test running whose runtime dependencies are unavailable.

    """
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)
    processor.start_measure(measure_with_tools)

    processor._thread.join()
    process_app_events()
    assert measure_with_tools.status == 'SKIPPED'


@pytest.mark.timeout(5)
def test_running_measure_failing_checks(processor, measure_with_tools):
    """Test running a measure failing to pass the tests.

    """
    measure_with_tools.pre_hooks['dummy'].fail_check = True
    processor.start_measure(measure_with_tools)

    processor._thread.join()
    process_app_events()
    assert measure_with_tools.status == 'FAILED'
    assert 'checks' in measure_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_running_measure_failing_pre_hooks(processor, measure_with_tools):
    """Test running a measure whose pre-hooks fail to execute.

    """
    measure_with_tools.pre_hooks['dummy'].fail_run = True
    processor.start_measure(measure_with_tools)

    pre_hook = measure_with_tools.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()
    pre_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure_with_tools.status == 'FAILED'
    assert 'pre-execution' in measure_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_running_measure_failing_main_task(processor, measure_with_tools):
    """Test running a measure whose pre-hooks fail to execute.

    """
    measure = measure_with_tools
    processor.engine = processor.plugin.create('engine', 'dummy')
    processor.engine.fail_perform = True
    processor.start_measure(measure_with_tools)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()
    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()

    assert measure.status == 'FAILED'
    assert 'main task' in measure_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_running_measure_failing_post_hooks(processor, measure_with_tools):
    """Test running a measure whose post-hooks fail to execute.

    """
    measure = measure_with_tools
    measure_with_tools.post_hooks['dummy'].fail_run = True
    processor.start_measure(measure_with_tools)
    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure_with_tools.status == 'FAILED'
    assert 'post-execution' in measure_with_tools.infos
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_running_forced_enqueued_measure(processor, measure_with_tools):
    """Test running a measure about which we know that checks are failing.

    """
    measure = measure_with_tools
    measure.forced_enqueued = True
    measure.pre_hooks['dummy'].fail_check = True
    processor.start_measure(measure_with_tools)
    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()


@pytest.mark.parametrize('mode', ['between hooks', 'after hooks'])
@pytest.mark.timeout(5)
def test_stopping_measure_while_preprocessing(mode, processor,
                                              measure_with_tools):
    """Test asking the processor to stop while is is running the pre-hooks.

    The post-hooks should not be run.

    """
    measure = measure_with_tools
    if mode == 'between hooks':
        # Will see the difference only in coverage
        measure.move_tool('pre-hook', 0, 1)
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()
    processor.stop_measure(no_post_exec=True)
    assert pre_hook.stop_called

    pre_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_stopping_measure_while_running_main(processor, measure_with_tools):
    """Test asking the processor to stop while is is running the main task.

    The post-hooks should be run.

    """
    measure = measure_with_tools
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.stop_measure()
    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_stopping_measure_while_postprocessing(processor, measure_with_tools):
    """Test asking the processor to stop while is is running the post hooks.

    """
    measure = measure_with_tools
    measure.add_tool('post-hook', 'dummy2')
    measure.post_hooks['dummy2'].fail_run = True
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)

    processor.stop_measure(force=True)
    assert post_hook.stop_called
    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


@pytest.mark.timeout(5)
def test_stopping_processing(processor, measure_with_tools):
    """Test stopping processing while running the main task..

    """
    plugin = processor.plugin.workbench.get_plugin('ecpy.measure')
    measure2 = Measure(plugin=plugin, root_task=RootTask(),
                       name='Dummy', id='002')
    processor.plugin.enqueued_measures.add(measure2)

    measure = measure_with_tools
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    pre_hook.go_on.set()

    wait_and_process(processor.engine.waiting.wait)

    processor.stop_processing(no_post_exec=True)
    processor.engine.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(5)
def test_stopping_processing_in_hook(processor, measure_with_tools):
    """Test stopping processing while running the main task..

    """
    plugin = processor.plugin.workbench.get_plugin('ecpy.measure')
    measure2 = Measure(plugin=plugin, root_task=RootTask(),
                       name='Dummy', id='002')
    processor.plugin.enqueued_measures.add(measure2)

    measure = measure_with_tools
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    processor.stop_processing(no_post_exec=True)
    pre_hook.go_on.set()

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(5)
def test_stopping_processing_while_in_pause(processor, measure_with_tools):
    """Test stopping processing while in pause before starting main.

    """
    plugin = processor.plugin.workbench.get_plugin('ecpy.measure')
    measure2 = Measure(plugin=plugin, root_task=RootTask(),
                       name='Dummy', id='002')
    processor.plugin.enqueued_measures.add(measure2)

    def wait_on_state_paused(timeout):
        return processor._state.wait(timeout, 'paused')

    measure = measure_with_tools
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    processor.pause_measure()
    pre_hook.accept_pause = False
    pre_hook.go_on.set()

    wait_and_process(wait_on_state_paused)

    processor.stop_processing(no_post_exec=True)
    sleep(0.2)

    def wait(timeout):
        processor._thread.join(timeout)
        return not processor._thread.is_alive()

    wait_and_process(wait)
    assert measure.status == 'INTERRUPTED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected

    assert measure2.status == 'READY'


@pytest.mark.timeout(15)
def test_pausing_measure(processor, measure_with_tools):
    """Test running a complete measure with pre/post-hooks and monitor.

    """
    measure = measure_with_tools
    measure.add_tool('pre-hook', 'dummy2')
    measure.move_tool('pre-hook', 2, 0)
    measure.add_tool('post-hook', 'dummy2')
    processor.start_measure(measure)

    def wait_on_state_paused(timeout):
        return processor._state.wait(timeout, 'paused')

    pre_hook = measure.pre_hooks['dummy2']
    assert pre_hook.waiting.wait(5)
    process_app_events()

    # Pause inside a pre_hook.
    processor.pause_measure()
    process_app_events()
    assert measure.status == 'PAUSING'
    pre_hook.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measure.status == 'PAUSED'

    processor.resume_measure()
    wait_and_process(pre_hook.signal_resuming.wait)
    assert measure.status == 'RESUMING'
    pre_hook.go_on_resuming.set()
    wait_and_process(pre_hook.signal_resumed.wait)
    assert measure.status == 'RUNNING'

    # Pause in between two pre_hooks
    processor.pause_measure()
    pre_hook.go_on_resumed.set()
    wait_and_process(wait_on_state_paused)
    assert measure.status == 'PAUSED'
    processor.resume_measure()

    # Pause just before starting the main measure.
    pre_hook2 = measure.pre_hooks['dummy']
    pre_hook2.accept_pause = False
    wait_and_process(pre_hook2.waiting.wait)
    assert measure.status == 'RUNNING'
    processor.pause_measure()
    pre_hook2.go_on.set()
    wait_and_process(wait_on_state_paused)
    processor.resume_measure()

    # Pause during the main task execution.
    wait_and_process(processor.engine.waiting.wait)
    processor.pause_measure()
    processor.engine.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measure.status == 'PAUSED'
    processor.resume_measure()
    wait_and_process(processor.engine.signal_resuming.wait)
    assert measure.status == 'RESUMING'
    processor.engine.go_on_resuming.set()
    wait_and_process(processor.engine.signal_resumed.wait)
    assert measure.status == 'RUNNING'
    processor.engine.go_on_resumed.set()

    # Pause inside a post_hook.
    post_hook = measure.post_hooks['dummy']
    wait_and_process(post_hook.waiting.wait)
    processor.pause_measure()
    process_app_events()
    assert measure.status == 'PAUSING'
    post_hook.go_on.set()
    wait_and_process(wait_on_state_paused)
    assert measure.status == 'PAUSED'

    processor.resume_measure()
    wait_and_process(post_hook.signal_resuming.wait)
    assert measure.status == 'RESUMING'
    post_hook.go_on_resuming.set()
    wait_and_process(post_hook.signal_resumed.wait)
    assert measure.status == 'RUNNING'

    # Pause in between two post_hooks
    processor.pause_measure()
    post_hook.go_on_resumed.set()
    wait_and_process(wait_on_state_paused)
    assert measure.status == 'PAUSED'
    processor.resume_measure()

    post_hook2 = measure.post_hooks['dummy2']
    wait_and_process(post_hook2.waiting.wait)
    post_hook2.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'COMPLETED'
    m = processor.plugin.workbench.get_manifest('test.measure')
    assert not m.find('runtime_dummy1').collected
    assert not m.find('runtime_dummy2').collected


def test_monitor_creation(processor, measure, dialog_sleep):
    """Test all possible possibilities when creating a monitor dock item.

    """
    def run(measure):
        t = Thread(target=processor._start_monitors, args=(measure,))
        t.start()
        while t.is_alive():
            process_app_events()
            sleep(0.001)
        process_app_events()
        sleep(dialog_sleep)

    processor.engine = processor.plugin.create('engine', 'dummy')

    measure.add_tool('monitor', 'dummy')
    run(measure)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measure.add_tool('monitor', 'dummy2')
    run(measure)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measure.remove_tool('monitor', 'dummy2')
    run(measure)
    assert len(processor.monitors_window.dock_area.dock_items()) == 1

    measure.add_tool('monitor', 'dummy3')
    run(measure)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2

    measure.add_tool('monitor', 'dummy4')
    run(measure)
    assert len(processor.monitors_window.dock_area.dock_items()) == 2
