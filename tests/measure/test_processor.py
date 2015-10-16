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
with enaml.imports():
    from enaml.workbench.ui.ui_manifest import UIManifest

    from ecpy.tasks.manager.manifest import TasksManagerManifest

from ..util import (ErrorDialogException, process_app_events)


@pytest.fixture
def processor(measure_workbench, measure):
    """Fixture starting the measure plugin and returning the processor.

    """
    # measure ensures that contributions are there
    measure_workbench.register(UIManifest())
    measure_workbench.register(TasksManagerManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')
    plugin.selected_engine = 'dummy'
    return plugin.processor


@pytest.mark.timeout(1)
def test_starting_measure_no_measure_enqueued(app, processor):
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


@pytest.mark.timeout(1)
def test_running_full_measure(app, processor, measure, tmpdir, windows):
    """Test running a complete measure with pre/post-hooks and monitor.

    """
    measure.add_tool('pre-hook', 'dummy')
    measure.add_tool('post-hook', 'dummy')
    measure.add_tool('monitor', 'dummy')
    measure.root_task.default_path = str(tmpdir)
    processor.start_measure(measure)

    pre_hook = measure.pre_hooks['dummy']
    assert pre_hook.waiting.wait(5)
    process_app_events()
    assert measure is processor.running_measure
    assert measure.status == 'RUNNING'
    assert tmpdir.listdir()

    pre_hook.go_on.set()

    i = 0
    while not processor.engine.waiting.wait(0.01):
        process_app_events()
        i += 1
        if i > 100:
            assert False
    process_app_events()

    assert processor.monitors_window
    assert processor.monitors_window.measure is measure
    assert measure.monitors['dummy'].running
#    sleep(5)
    processor.engine.go_on.set()

    post_hook = measure.post_hooks['dummy']
    i = 0
    while not post_hook.waiting.wait(0.01):
        process_app_events()  # Needed to close monitors
        i += 1
        if i > 100:
            assert False
    process_app_events()

    assert measure.task_execution_result
    assert not measure.monitors['dummy'].running
    assert measure.monitors['dummy'].received_news

    post_hook.go_on.set()

    processor._thread.join()
    process_app_events()
    assert measure.status == 'COMPLETED'


def test_running_measure_whose_runtime_are_unavailable(processor, measure):
    pass


def test_running_measure_failing_checks(processor, measure):
    pass


def test_running_measure_failing_pre_hooks(processor, measure):
    pass


def test_running_measure_failing_post_hooks(processor, measure):
    pass

# Test not running post-hook based on state


def test_stopping_measure(processor, measure):
    """
    """
    pass


def test_stopping_processing(processor, measure):
    """
    """
    pass


def test_pausing_measure(processor, measure):
    """
    """
    pass

# Test monitor creation there is a number of cases
