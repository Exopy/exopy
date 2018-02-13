# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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

from exopy.tasks.tasks.base_tasks import RootTask, ComplexTask
with enaml.imports():
    from exopy.tasks.tasks.base_views import RootTaskView
    from exopy.tasks.widgets.building import BuilderView

from exopy.testing.util import (show_widget, process_app_events, handle_dialog,
                               get_window)


pytest_plugins = str('exopy.testing.tasks.fixtures'),


@pytest.mark.ui
def test_root_path_edition(windows, task_workbench, dialog_sleep,
                           monkeypatch):
    """Test the behavior of the root task view.

    """
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))

    butt = view.widgets()[2]

    @classmethod
    def choose_path(cls, **kwargs):
        return 'test/path'
    with enaml.imports():
        from exopy.tasks.tasks.base_views import FileDialogEx
    monkeypatch.setattr(FileDialogEx, 'get_existing_directory',
                        choose_path)

    butt.clicked = True
    assert task.default_path == 'test/path'

    @classmethod
    def choose_path(cls, **kwargs):
        return ''
    monkeypatch.setattr(FileDialogEx, 'get_existing_directory',
                        choose_path)

    butt.clicked = True
    assert task.default_path == 'test/path'

    @classmethod
    def choose_path(cls, **kwargs):
        return ''
    monkeypatch.setattr(FileDialogEx, 'get_existing_directory',
                        choose_path)


@pytest.mark.ui
def test_root_view(windows, task_workbench, dialog_sleep):
    """Test the behavior of the root task view.

    """
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))
    editor = view.children[-1]

    win = show_widget(view)
    sleep(dialog_sleep)
    assert editor.task is task
    assert editor.root is view

    TASK_NAME = 'Foo'

    def answer_dialog(dial):
        selector = dial.selector
        selector.selected_task = 'exopy.ComplexTask'
        dial.config.task_name = TASK_NAME
        process_app_events()

    with handle_dialog('accept', answer_dialog, cls=BuilderView):
        editor._empty_button.clicked = True
    process_app_events()
    assert task.children
    assert type(task.children[0]) is ComplexTask
    assert len(editor._children_buttons) == 1
    sleep(dialog_sleep)

    TASK_NAME = 'Bar'
    with handle_dialog('accept', answer_dialog, cls=BuilderView):
        editor.operations['add'](0, 'after')
    process_app_events()
    sleep(dialog_sleep)

    task.children[0].add_child_task(0, ComplexTask(name='Test'))
    get_window().maximize()
    process_app_events()
    sleep(dialog_sleep)

    editor.operations['move'](0, 1)
    process_app_events()
    sleep(dialog_sleep)

    task.remove_child_task(1)
    process_app_events()
    sleep(dialog_sleep)
    assert len(view._cache) == 2

    # Test removing the last child and removing a view for an already removed
    # task
    child_task = task.children[0]
    editor.operations['remove'](0)
    process_app_events()
    sleep(dialog_sleep)
    assert len(view._cache) == 1

    view.discard_view(child_task)

    win.close()


@pytest.mark.ui
def test_swapping(windows, task_workbench, dialog_sleep):
    """Test moving a view between containers.

    """
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
    sleep(dialog_sleep)

    view.set_parent(None)
    subview.set_parent(cont)
    subview.refresh()
    process_app_events()
    assert cont.children == [subview]
    sleep(dialog_sleep)

    subview.set_parent(None)
    view.set_parent(cont)
    view.refresh()
    process_app_events()
    assert cont.children == [view]
    assert subview.visible
    sleep(dialog_sleep)
