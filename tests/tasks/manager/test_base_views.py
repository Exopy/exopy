# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the functionment of most basic views.

As task views need an active workbench, tests are located here to avoid moving
the request for the manager at the root.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml

from ecpy.tasks.base_tasks import RootTask, ComplexTask
with enaml.imports():
    from ecpy.tasks.base_views import RootTaskView

from ...util import show_widget, process_app_events, handle_dialog


def test_root_view(windows, task_workbench):
    """Test the behavior of the root task view.

    """
    from ...conftest import DIALOG_SLEEP
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))
    editor = view.children[0]

    show_widget(view)
    sleep(DIALOG_SLEEP)
    assert editor.task is task
    assert editor.root is view

    def answer_dialog(dial):
        selector = dial.selector
        selector.selected_task = 'ComplexTask'
        dial.config.task_name = 'Test'
        process_app_events()

    with handle_dialog('accept', answer_dialog):
        editor._empty_button.clicked = True
    process_app_events()
    assert task.children
    assert type(task.children[0]) is ComplexTask
    assert len(editor._children) == 1
    sleep(DIALOG_SLEEP)

    editor.operations['add'](0, 'after')
    process_app_events()
    sleep(DIALOG_SLEEP)

    task.children[0].add_child_task(0, ComplexTask())
    process_app_events()
    sleep(DIALOG_SLEEP)

    editor.operations['move'](0, 1)

    editor.operations['remove'](1)
    assert len(view._cache) == 2
