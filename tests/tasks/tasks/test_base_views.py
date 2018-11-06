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
import pytest
import enaml
from enaml.widgets.api import Container

from exopy.tasks.tasks.base_tasks import RootTask, ComplexTask
with enaml.imports():
    from exopy.tasks.tasks.base_views import RootTaskView
    from exopy.tasks.widgets.building import BuilderView

from exopy.testing.util import show_widget, handle_dialog, get_window


@pytest.mark.ui
def test_root_path_edition(exopy_qtbot, task_workbench, dialog_sleep,
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
def test_root_view(exopy_qtbot, task_workbench, dialog_sleep):
    """Test the behavior of the root task view.

    """
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))
    editor = view.children[-1]

    win = show_widget(exopy_qtbot, view)
    exopy_qtbot.wait(dialog_sleep)
    assert editor.task is task
    assert editor.root is view

    TASK_NAME = 'Foo'

    def answer_dialog(bot, dial):
        selector = dial.selector
        selector.selected_task = 'exopy.ComplexTask'
        dial.config.task_name = TASK_NAME

    with handle_dialog(exopy_qtbot, 'accept', answer_dialog, cls=BuilderView):
        editor._empty_button.clicked = True

    def assert_task_children():
        assert task.children
    exopy_qtbot.wait_until(assert_task_children)
    assert type(task.children[0]) is ComplexTask
    assert len(editor._children_buttons) == 1
    exopy_qtbot.wait(dialog_sleep)

    TASK_NAME = 'Bar'
    with handle_dialog(exopy_qtbot, 'accept', answer_dialog, cls=BuilderView):
        editor.operations['add'](0, 'after')
    exopy_qtbot.wait(10)
    exopy_qtbot.wait(dialog_sleep)

    task.children[0].add_child_task(0, ComplexTask(name='Test'))
    get_window(exopy_qtbot).maximize()
    exopy_qtbot.wait(10)
    exopy_qtbot.wait(dialog_sleep)

    editor.operations['move'](0, 1)
    exopy_qtbot.wait(10)
    exopy_qtbot.wait(dialog_sleep)

    task.remove_child_task(1)
    exopy_qtbot.wait(10)
    exopy_qtbot.wait(dialog_sleep)
    assert len(view._cache) == 2

    # Test removing the last child and removing a view for an already removed
    # task
    child_task = task.children[0]
    editor.operations['remove'](0)
    exopy_qtbot.wait(10)
    exopy_qtbot.wait(dialog_sleep)
    assert len(view._cache) == 1

    view.discard_view(child_task)

    win.close()


@pytest.mark.ui
def test_swapping(exopy_qtbot, task_workbench, dialog_sleep):
    """Test moving a view between containers.

    """
    task = RootTask()
    view = RootTaskView(task=task,
                        core=task_workbench.get_plugin('enaml.workbench.core'))

    subtask = ComplexTask(name='Test')
    subview = view.view_for(subtask)

    task.add_child_task(0, subtask)

    cont = Container()

    show_widget(exopy_qtbot, cont)
    view.set_parent(cont)
    view.refresh()

    def assert_children():
        assert cont.children == [view]
    exopy_qtbot.wait_until(assert_children)
    exopy_qtbot.wait(dialog_sleep)

    view.set_parent(None)
    subview.set_parent(cont)
    subview.refresh()

    def assert_children():
        assert cont.children == [subview]
    exopy_qtbot.wait_until(assert_children)
    exopy_qtbot.wait(dialog_sleep)

    subview.set_parent(None)
    view.set_parent(cont)
    view.refresh()

    def assert_children():
        assert cont.children == [view]
    exopy_qtbot.wait_until(assert_children)
    assert subview.visible
    exopy_qtbot.wait(dialog_sleep)
