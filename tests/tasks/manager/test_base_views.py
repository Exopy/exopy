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

import pytest
import enaml
from enaml.widgets.api import Container

from ecpy.tasks.base_tasks import RootTask, ComplexTask
with enaml.imports():
    from ecpy.tasks.base_views import RootTaskView

from ...util import show_widget, process_app_events, handle_dialog, get_window


@pytest.mark.ui
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

    TASK_NAME = 'Foo'

    def answer_dialog(dial):
        selector = dial.selector
        selector.selected_task = 'ComplexTask'
        dial.config.task_name = TASK_NAME
        process_app_events()

    with handle_dialog('accept', answer_dialog):
        editor._empty_button.clicked = True
    process_app_events()
    assert task.children
    assert type(task.children[0]) is ComplexTask
    assert len(editor._children_buttons) == 1
    sleep(DIALOG_SLEEP)

    TASK_NAME = 'Bar'
    with handle_dialog('accept', answer_dialog):
        editor.operations['add'](0, 'after')
    process_app_events()
    sleep(DIALOG_SLEEP)

    task.children[0].add_child_task(0, ComplexTask(name='Test'))
    get_window().maximize()
    process_app_events()
    sleep(DIALOG_SLEEP)

    editor.operations['move'](0, 1)

    task.children[1].remove_child_task(0)
    assert len(view._cache) == 2

    editor.operations['remove'](0)
    assert len(view._cache) == 1


@pytest.mark.ui
def test_swapping(app, task_workbench):
    """Test moving a view between containers.

    """
    from ...conftest import DIALOG_SLEEP
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))

    subtask = ComplexTask(name='Test')
    subview = view.view_for(subtask)

    task.add_child_task(0, subtask)

    cont = Container()

    show_widget(cont)
    view.set_parent(cont)
    view.refresh()
    process_app_events()
    assert cont.children == [view]
    sleep(DIALOG_SLEEP)

    view.set_parent(None)
    subview.set_parent(cont)
    subview.refresh()
    process_app_events()
    assert cont.children == [subview]
    sleep(DIALOG_SLEEP)

    subview.set_parent(None)
    view.set_parent(cont)
    view.refresh()
    process_app_events()
    assert cont.children == [view]
    assert subview.visible
    sleep(DIALOG_SLEEP)
