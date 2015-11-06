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
from ecpy.measure.editors.api import Editor
from ecpy.measure.editors.execution_editor.editor_model import\
     ExecutionEditorModel

from ...util import process_app_events

with enaml.imports():
    from ecpy.measure.editors.execution_editor import ExecutionEditor
    from .testing_window import EditorTestingWindow


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
    model._children_observer(ContainerChange(collapsed=[ContainerChange()]))


def test_execution_editor_widget(windows, task, dialog_sleep):
    """Test the behavior of the execution editor widget.

    """
    editor = ExecutionEditor(declaration=Editor(id='ecpy.execution_editor'),
                             selected_task=task)
    window = EditorTestingWindow(editor=editor)
    window.show()
    process_app_events()
    sleep(dialog_sleep)
