# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the capabilities of the execution editor model.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.utils.container_change import ContainerChange
from ecpy.tasks.api import RootTask, ComplexTask, SimpleTask
from ecpy.tasks.tasks.logic.loop_task import LoopTask
from ecpy.measure.editors.api import Editor
from ecpy.measure.editors.execution_editor.editor_model import\
     ExecutionEditorModel

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.measure.editors.execution_editor import ExecutionEditor
    from ecpy.testing.windows import PageTestingWindow


@pytest.fixture
def task():
    """Create a basic task hierarchy for testing.

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
    assert model.pools == ['test', 'test2']

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
    assert sorted(model.pools) == ['test', 'test2', 'test3']

    task.remove_child_task(0)
    assert model.pools == ['test']

    model.root = None
    task.children[0].parallel = {'activated': True, 'pool': 'test2'}
    assert 'test2' not in model.pools

    # For coverage
    notification = ContainerChange(collapsed=[ContainerChange()])
    model._child_notifier_observer(notification)


def test_execution_editor_widget(windows, task, dialog_sleep):
    """Test the behavior of the execution editor widget.

    """
    dialog_sleep = dialog_sleep or 1
    task.children[1].children[0].parallel = {}

    def get_task_widget(editor):
        return editor.page_widget().widgets()[0].scroll_widget().widgets()[0]

    editor = ExecutionEditor(declaration=Editor(id='ecpy.execution_editor'),
                             selected_task=task)
    window = PageTestingWindow(widget=editor)
    window.show()
    process_app_events()
    sleep(dialog_sleep)

    ctask = task.children[1]
    editor.selected_task = ctask
    process_app_events()
    sleep(dialog_sleep)

    ced = get_task_widget(editor)
    ced.widgets()[0].checked = not ctask.stoppable
    process_app_events()
    assert ced.widgets()[0].checked == ctask.stoppable
    sleep(dialog_sleep)

    ctask.parallel['pool'] = 'test_'
    ced.widgets()[1].checked = True
    process_app_events()
    assert 'test_' in editor.pool_model.pools
    sleep(dialog_sleep)

    ced.widgets()[3].checked = False
    process_app_events()
    sleep(dialog_sleep)
    ctask.wait['no_wait'] = ['test2']
    ced.widgets()[3].checked = True
    process_app_events()
    assert 'test2' in editor.pool_model.pools
    sleep(dialog_sleep)

    ced.widgets()[2].selected = 'test2'
    process_app_events()
    assert 'test' not in editor.pool_model.pools
    sleep(dialog_sleep)

    def get_popup_content(parent):
        return parent.children[-1].central_widget().widgets()

    ced.widgets()[2].children[0].children[0].triggered = True
    process_app_events()
    sleep(dialog_sleep)
    process_app_events()  # So that the popup shows correctly
    popup_content = get_popup_content(ced.widgets()[2])
    popup_content[0].text = 'test3'
    popup_content[1].clicked = True
    process_app_events()
    assert 'test3' in editor.pool_model.pools
    sleep(dialog_sleep)
    process_app_events()  # So that the popup is closed correctly

    ced.widgets()[2].children[0].children[0].triggered = True
    process_app_events()
    sleep(dialog_sleep)
    process_app_events()  # So that the popup shows correctly
    popup_content = get_popup_content(ced.widgets()[2])
    popup_content[0].text = 'test4'
    popup_content[2].clicked = True
    process_app_events()
    assert 'test4' not in editor.pool_model.pools
    sleep(dialog_sleep)
    process_app_events()  # So that the popup is closed correctly

    assert ced.widgets()[4].checked is False
    ced.widgets()[4].checked = True
    process_app_events()
    assert 'wait' in ctask.wait and 'no_wait' not in ctask.wait
    sleep(dialog_sleep)

    ced.widgets()[7].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    popup_content = get_popup_content(ced.widgets()[7])
    check_box = popup_content[0].scroll_widget().widgets()[1]
    assert not check_box.checked
    check_box.checked = True
    process_app_events()
    sleep(dialog_sleep)
    popup_content[-2].clicked = True
    process_app_events()
    assert 'test3' in ctask.wait['wait']
    sleep(dialog_sleep)

    ced.widgets()[7].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    popup_content = get_popup_content(ced.widgets()[7])
    check_box = popup_content[0].scroll_widget().widgets()[2]
    assert not check_box.checked
    check_box.checked = True
    process_app_events()
    sleep(dialog_sleep)
    popup_content[-1].clicked = True
    process_app_events()
    assert 'test_' not in ctask.wait['wait']
    sleep(dialog_sleep)

    editor.selected_task = task
    task.remove_child_task(1)
    process_app_events()
    assert ctask not in editor._cache
    sleep(dialog_sleep)

    editor.ended = True
