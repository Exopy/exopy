# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the LoopTask specific configurer.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.testing.util import (show_and_close_widget, show_widget,
                               process_app_events)
from ecpy.tasks.configs.loop_config import (LoopTaskConfig)
with enaml.imports():
    from ecpy.tasks.configs.loop_config_view import LoopConfigView


@pytest.mark.ui
def test_loop_config(app, task_workbench):
    """Test the loop config.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('ecpy.LoopTask'))

    assert config.task_name
    assert config.ready
    assert config.task_doc

    config.task_name = ''
    assert not config.ready

    config.task_name = 'Test'
    task = config.build_task()
    assert task.name == 'Test'

    plugin.auto_task_names = []
    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('ecpy.LoopTask'))

    assert not config.task_name
    assert not config.ready

    show_and_close_widget(LoopConfigView(config=config))


@pytest.mark.ui
def test_loop_config_with_subtask(task_workbench, windows, dialog_sleep,
                                  monkeypatch):
    """Test the loop config.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('ecpy.LoopTask'),
                            task_name='Test')

    show_widget(LoopConfigView(config=config))
    assert config.ready
    sleep(dialog_sleep)

    config.use_subtask = True
    assert not config.ready
    process_app_events()
    sleep(dialog_sleep)

    config.subtask = 'ecpy.BreakTask'
    assert config.ready
    process_app_events()
    sleep(dialog_sleep)

    def dummy(self):
        self.ready = False

    monkeypatch.setattr(type(config.subconfig), 'check_parameters',
                        dummy)
    config.task_name = 'Bis'
    assert config.subconfig.task_name == 'Bis'  # Check sync
    assert not config.ready  # Result from the monkeypatch
    process_app_events()
    sleep(dialog_sleep)

    config.use_subtask = False
    assert config.ready
    process_app_events()
    sleep(dialog_sleep)

    config.use_subtask = True
    config.subtask = 'ecpy.ContinueTask'
    task = config.build_task()
    assert task.name == 'Bis'
    assert type(task.task).__name__ == 'ContinueTask'
