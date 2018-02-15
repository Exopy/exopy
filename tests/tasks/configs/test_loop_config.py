# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the LoopTask specific configurer.

"""
import enaml

from exopy.testing.util import show_and_close_widget, show_widget
from exopy.tasks.configs.loop_config import (LoopTaskConfig)
with enaml.imports():
    from exopy.tasks.configs.loop_config_view import LoopConfigView


def test_loop_config(exopy_qtbot, task_workbench):
    """Test the loop config.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')

    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('exopy.LoopTask'))

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
                            task_class=plugin.get_task('exopy.LoopTask'))

    assert not config.task_name
    assert not config.ready

    show_and_close_widget(exopy_qtbot, LoopConfigView(config=config))


def test_loop_config_with_subtask(task_workbench, exopy_qtbot, dialog_sleep,
                                  monkeypatch):
    """Test the loop config.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')

    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('exopy.LoopTask'),
                            task_name='Test')

    show_widget(exopy_qtbot, LoopConfigView(config=config))
    assert config.ready
    exopy_qtbot.wait(dialog_sleep)

    config.use_subtask = True
    assert not config.ready
    exopy_qtbot.wait(dialog_sleep + 100)

    config.subtask = 'exopy.BreakTask'
    assert config.ready
    exopy_qtbot.wait(dialog_sleep + 100)

    def dummy(self):
        self.ready = False

    monkeypatch.setattr(type(config.subconfig), 'check_parameters',
                        dummy)
    config.task_name = 'Bis'
    assert config.subconfig.task_name == 'Bis'  # Check sync
    assert not config.ready  # Result from the monkeypatch
    exopy_qtbot.wait(dialog_sleep + 100)

    config.use_subtask = False
    assert config.ready
    exopy_qtbot.wait(dialog_sleep + 100)

    config.use_subtask = True
    config.subtask = 'exopy.ContinueTask'
    task = config.build_task()
    assert task.name == 'Bis'
    assert type(task.task).__name__ == 'ContinueTask'
