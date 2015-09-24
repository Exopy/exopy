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

from ecpy.tasks.manager.configs.loop_config import (LoopTaskConfig)
with enaml.imports():
    from ecpy.tasks.manager.configs.loop_config_view import LoopConfigView

from ....util import show_and_close_widget, show_widget, process_app_events


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
def test_loop_config_with_subtask(task_workbench, windows):
    """Test the loop config.

    """
    from ....conftest import DIALOG_SLEEP
    plugin = task_workbench.get_plugin('ecpy.tasks')

    config = LoopTaskConfig(manager=plugin,
                            task_class=plugin.get_task('ecpy.LoopTask'),
                            task_name='Test')

    show_widget(LoopConfigView(config=config))
    assert config.ready
    sleep(DIALOG_SLEEP)

    config.use_subtask = True
    assert not config.ready
    process_app_events()
    sleep(DIALOG_SLEEP)

    config.subtask = 'ecpy.BreakTask'
    assert config.ready
    process_app_events()
    sleep(DIALOG_SLEEP)

    config.subconfig.task_name = ''
    assert not config.ready
    process_app_events()
    sleep(DIALOG_SLEEP)

    config.use_subtask = False
    assert config.ready
    process_app_events()
    sleep(DIALOG_SLEEP)

    config.use_subtask = True
    config.subtask = 'ecpy.ContinueTask'
    task = config.build_task()
    assert task.name == 'Test'
    assert type(task.task).__name__ == 'ContinueTask'
