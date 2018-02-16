# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the capabilities of the execution editor model.

"""
import pytest
import enaml

from exopy.utils.container_change import ContainerChange
from exopy.tasks.api import RootTask, ComplexTask, SimpleTask
from exopy.tasks.tasks.logic.loop_task import LoopTask
from exopy.measurement.editors.api import Editor
from exopy.measurement.editors.execution_editor.editor_model import\
     ExecutionEditorModel

from exopy.testing.util import (wait_for_window_displayed, get_popup,
                                wait_for_destruction)

with enaml.imports():
    from exopy.measurement.editors.execution_editor import ExecutionEditor
    from exopy.testing.windows import PageTestingWindow


@pytest.fixture
def task():
    """Create a basic task hierarchy for testing.

    Root
      - SimpleTask: parallel=False, wait=False
      - ComplexTask: parallel=False, wait=True
        - SimpleTask: parallel=True, wait= False

    """
    root = RootTask()
    root.add_child_task(0, SimpleTask(name='simp1'))

    comp = ComplexTask(name='comp1',
                       wait={'activated': True, 'no_wait': ['test']})
    comp.add_child_task(0, SimpleTask(name='simp2',
                                      parallel={'activated': True,
                                                'pool': 'test'}))

    root.add_child_task(1, comp)
    return root


def test_model_observe_parallel(task):
    """Test that the model is properly updated when the parallel setting of a
    task changes.

    """
    model = ExecutionEditorModel(root=task)
    assert model.pools == ['test']

    task.children[0].parallel = {'activated': True, 'pool': 'test2'}
    assert 'test2' in model.pools

    task.children[0].parallel = {'activated': False, 'pool': 'test2'}
    assert 'test2' not in model.pools

    model.unbind_observers()
    task.children[0].parallel = {'activated': True, 'pool': 'test2'}
    assert 'test2' not in model.pools


def test_model_observe_wait(task):
    """Test that the model is properly updated when the wait setting of a task
    change.

    """
    model = ExecutionEditorModel(root=task)
    assert model.pools == ['test']

    child = task.children[1].children[0]

    child.wait = {'activated': True, 'wait': ['test2']}
    assert 'test2' in model.pools

    child.wait = {'activated': False, 'wait': ['test2']}
    assert 'test2' not in model.pools

    child.wait = {'activated': True, 'no_wait': ['test2']}
    assert 'test2' in model.pools

    child = task.children[1]

    child.wait = {'activated': True, 'wait': ['test3']}
    assert 'test3' in model.pools

    child.wait = {'activated': False, 'wait': ['test3']}
    assert 'test3' not in model.pools


def test_model_observe_child_member(task):
    """Test that replacing a child does trigger the expected behavior.

    """
    model = ExecutionEditorModel(root=task)
    assert model.pools == ['test']

    c = LoopTask(name='comp2', parallel={'activated': True,
                                         'pool': 'test2'})
    task.add_child_task(2, c)
    assert 'test2' in model.pools

    c.children = [SimpleTask(name='simp3', parallel={'activated': True,
                                                     'pool': 'test3'})]
    assert 'test3' in model.pools

    c.children = []
    assert sorted(model.pools) == sorted(['test', 'test2'])

    c.task = SimpleTask(name='simp3', parallel={'activated': True,
                                                'pool': 'test4'})
    assert 'test4' in model.pools

    c.task = None
    assert sorted(model.pools) == sorted(['test', 'test2'])


def test_model_observe_child_adding_removing(task):
    """Test that adding removing a child does trigger the expected behavior.

    """
    model = ExecutionEditorModel(root=task)
    assert model.pools == ['test']

    c = ComplexTask(name='comp2', parallel={'activated': True,
                                            'pool': 'test2'})
    task.add_child_task(2, c)
    assert 'test2' in model.pools

    c.add_child_task(0, SimpleTask(name='simp3', parallel={'activated': True,
                                                           'pool': 'test3'}))
    assert 'test3' in model.pools

    task.move_child_task(2, 0)
    assert sorted(model.pools) == sorted(['test', 'test2', 'test3'])

    task.remove_child_task(0)
    assert model.pools == ['test']

    model.root = None
    task.children[0].parallel = {'activated': True, 'pool': 'test2'}
    assert 'test2' not in model.pools

    # For coverage
    notification = ContainerChange(collapsed=[ContainerChange()])
    model._child_notifier_observer(notification)


def test_execution_editor_widget(exopy_qtbot, task, dialog_sleep):
    """Test the behavior of the execution editor widget.

    """
    task.children[1].children[0].parallel = {}

    def get_task_widget(editor):
        """Get the widget associated with the currently selected task.

        """
        return editor.page_widget().widgets()[0].scroll_widget().widgets()[0]

    editor = ExecutionEditor(declaration=Editor(id='exopy.execution_editor'),
                             selected_task=task)
    window = PageTestingWindow(widget=editor)
    window.show()
    wait_for_window_displayed(exopy_qtbot, window)
    exopy_qtbot.wait(dialog_sleep)

    # Select the complex task (ref ctask)
    ctask = task.children[1]
    editor.selected_task = ctask
    exopy_qtbot.wait(10 + dialog_sleep)

    # Get the widget (ced) associated with ctask and alter the stoppable
    # setting and the change propagation
    ced = get_task_widget(editor)
    ced.widgets()[0].checked = not ctask.stoppable

    def assert_stoppable():
        assert ced.widgets()[0].checked == ctask.stoppable
    exopy_qtbot.wait_until(assert_stoppable)
    exopy_qtbot.wait(dialog_sleep)

    # Ask the editor to hide its children by clicking the button (this does
    # not check that the layout actually changed simply that is is correct)
    full_ced = ced.parent
    full_ced.widgets()[-2].clicked = True
    assert full_ced.widgets()[-1].visible is False
    assert not full_ced.widgets()[-1].layout_constraints()

    # Undo
    full_ced.widgets()[-2].clicked = True
    assert full_ced.widgets()[-1].visible is True
    assert full_ced.widgets()[-1].layout_constraints()

    # Set the complex task in parallel and check the update of the list of
    # pools
    ctask.parallel['pool'] = 'test_'
    ced.widgets()[1].checked = True

    def assert_pools():
        assert 'test_' in editor.pool_model.pools
    exopy_qtbot.wait_until(assert_pools)
    exopy_qtbot.wait(dialog_sleep)

    # Unset the wait setting, change the waiting pool, set the wait and check
    # the list of pools
    ced.widgets()[3].checked = False
    exopy_qtbot.wait(10 + dialog_sleep)
    ctask.wait['no_wait'] = ['test2']
    ced.widgets()[3].checked = True

    def assert_pools():
        assert 'test2' in editor.pool_model.pools
    exopy_qtbot.wait_until(assert_pools)
    exopy_qtbot.wait(dialog_sleep)

    # Change the selected pool for parallel and check the list of pools
    ced.widgets()[2].selected = 'test2'

    def assert_pools():
        assert 'test' not in editor.pool_model.pools
    exopy_qtbot.wait_until(assert_pools)
    exopy_qtbot.wait(dialog_sleep)

    def get_popup_content(popup):
        return popup.central_widget().widgets()

    # Create a new pool using the context menu on parallell
    ced.widgets()[2].children[0].children[0].triggered = True
    popup = get_popup(exopy_qtbot)
    popup_content = get_popup_content(popup)
    popup_content[0].text = 'test3'
    popup_content[1].clicked = True

    def assert_pools():
        assert 'test3' in editor.pool_model.pools
    exopy_qtbot.wait_until(assert_pools)
    exopy_qtbot.wait(dialog_sleep)
    wait_for_destruction(exopy_qtbot, popup)

    # Create a new pool using the context menu on parallell, but cancel it
    ced.widgets()[2].children[0].children[0].triggered = True
    popup = get_popup(exopy_qtbot)
    popup_content = get_popup_content(popup)
    popup_content[0].text = 'test4'
    popup_content[2].clicked = True

    def assert_pools():
        assert 'test4' not in editor.pool_model.pools
    exopy_qtbot.wait_until(assert_pools)
    exopy_qtbot.wait(dialog_sleep)
    wait_for_destruction(exopy_qtbot, popup)

    # Check we were set on no_wait and switch to wait
    assert ced.widgets()[4].widgets()[0].checked is False
    ced.widgets()[4].widgets()[0].checked = True

    def assert_wait():
        assert 'wait' in ctask.wait and 'no_wait' not in ctask.wait
    exopy_qtbot.wait_until(assert_wait)
    exopy_qtbot.wait(dialog_sleep)

    # Use the popup to edit the list of pools on which to wait.
    # Click ok at the end
    btt = ced.widgets()[4].widgets()[-1]  # ref to the push button
    btt.clicked = True
    popup = get_popup(exopy_qtbot)
    popup_content = get_popup_content(popup)
    check_box = popup_content[0].scroll_widget().widgets()[1]
    assert not check_box.checked
    check_box.checked = True
    exopy_qtbot.wait(10 + dialog_sleep)
    popup_content[-2].clicked = True

    def assert_wait():
        assert 'test3' in ctask.wait['wait']
    exopy_qtbot.wait_until(assert_wait)
    wait_for_destruction(exopy_qtbot, popup)
    exopy_qtbot.wait(dialog_sleep)

    # Use the popup to edit the list of pools on which to wait.
    # Click cancel at the end
    btt.clicked = True
    popup = get_popup(exopy_qtbot)
    popup_content = get_popup_content(popup)
    check_box = popup_content[0].scroll_widget().widgets()[2]
    assert not check_box.checked
    check_box.checked = True
    exopy_qtbot.wait(10 + dialog_sleep)
    popup_content[-1].clicked = True

    def assert_wait():
        assert 'test_' not in ctask.wait['wait']
    exopy_qtbot.wait_until(assert_wait)
    wait_for_destruction(exopy_qtbot, popup)
    exopy_qtbot.wait(dialog_sleep)

    # Test moving a task and switching between different editors
    editor.selected_task = task
    task.move_child_task(0, 1)
    exopy_qtbot.wait(10 + dialog_sleep)
    editor.selected_task = task.children[0]
    exopy_qtbot.wait(10 + dialog_sleep)
    editor.selected_task = task.children[1]
    exopy_qtbot.wait(10 + dialog_sleep)
    editor.selected_task = task

    # Test removing a task and switching between different editors
    # First select the ctask child so that its view is not parented to the view
    editor.selected_task = ctask.children[0]

    # Then select a task that will not reparent it
    editor.selected_task = task.children[0]
    task.remove_child_task(0)
    exopy_qtbot.wait(10 + dialog_sleep)
    editor.selected_task = task.children[0]
    exopy_qtbot.wait(10 + dialog_sleep)
    editor.selected_task = task
    exopy_qtbot.wait(10 + dialog_sleep)
    assert ctask not in editor._cache
    # Try removing again this view which should not crash
    editor.discard_view(task)
    # Check the view was properly destroyed and removed
    assert ctask.children[0] not in editor._cache

    editor.ended = True
