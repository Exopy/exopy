# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the capabilities of the database access editor model.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.utils.container_change import ContainerChange
from ecpy.tasks.api import RootTask, ComplexTask, SimpleTask
from ecpy.measure.editors.api import Editor
from ecpy.measure.editors.database_access_editor.editor_model import\
     EditorModel

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.measure.editors.database_access_editor import\
        DatabaseAccessEditor
    from ecpy.testing.windows import PageTestingWindow


@pytest.fixture
def task():
    r = RootTask()
    r.add_child_task(0, SimpleTask(name='simp1', database_entries={'t': 1}))
    c = ComplexTask(name='comp1', database_entries={'t1': 2, 't2': 'r'})
    c.add_child_task(0,
                     SimpleTask(name='simp2', database_entries={'t': 1}))
    c2 = ComplexTask(name='comp2', database_entries={'t1': 2, 't2': 'r'})
    c2.add_child_task(0,
                      SimpleTask(name='simp3', database_entries={'t': 1}))
    c.add_child_task(1, c2)
    r.add_child_task(1, c)
    return r


def test_node_sorting(task):
    """Test that a node model correctly order its children and react to
    task re-ordering.

    """
    ed = EditorModel(root=task)
    nmodel = ed.nodes['root']
    task.add_child_task(0, ComplexTask(name='cc'))
    nmodel.sort_nodes()
    assert [c.task.name for c in nmodel.children] == ['cc', 'comp1']
    assert sorted(nmodel.entries) == sorted(['default_path', 'simp1_t',
                                             'comp1_t1', 'comp1_t2'])

    task.move_child_task(0, 2)
    assert [c.task.name for c in nmodel.children] == ['comp1', 'cc']
    assert (sorted(nmodel.children[0].entries) ==
            sorted(['simp2_t', 'comp2_t1', 'comp2_t2']))

    change = ContainerChange(collapsed=[ContainerChange()])
    nmodel._react_to_task_children_event(change)  # For coverage


def test_editor_modifying_exception_level(task):
    """Test modifying the level of an access exception.

    """
    ed = EditorModel(root=task)
    rnode = ed.nodes['root']

    node = rnode.children[0].children[0]
    # Check that we can desambiguate between task with same prefix
    node.task.add_child_task(0, SimpleTask(name='simp3_t',
                                           database_entries={'t': 1}))
    node.add_exception('simp3_t')
    assert 'simp3_t' in node.parent.exceptions
    assert 't' in node.task.children[1].access_exs

    ed.increase_exc_level('root/comp1', 'simp3_t')
    assert 'simp3_t' not in node.parent.exceptions
    assert 'simp3_t' in node.parent.parent.exceptions

    ed.decrease_exc_level('root', 'simp3_t')
    assert 'simp3_t' in node.parent.exceptions
    assert 'simp3_t' not in node.parent.parent.exceptions

    ed.decrease_exc_level('root/comp1', 'simp3_t')
    assert 'simp3_t' not in node.parent.exceptions
    assert 't' not in node.task.children[1].access_exs

    node.parent.add_exception('simp2_t')
    assert 'simp2_t' in node.parent.parent.exceptions


def test_editor_changing_root(task):
    """Setting a new root.

    """
    ed = EditorModel(root=RootTask())
    assert len(ed.nodes) == 1

    ed.root = task
    assert len(ed.nodes) == 3
    assert ('root' in ed.nodes and 'root/comp1' in ed.nodes and
            'root/comp1/comp2' in ed.nodes)
    assert ed.nodes['root/comp1'] in ed.nodes['root'].children
    assert ed.nodes['root/comp1/comp2'] in ed.nodes['root/comp1'].children


def test_handling_entry_modification(task):
    """Test handling the possible modifications at the entry level.

    """
    ed = EditorModel(root=task)

    child = task.children[1].children[0]
    entries = child.database_entries.copy()
    entries['t2'] = 1
    child.database_entries = entries

    assert 'simp2_t2' in ed.nodes['root/comp1'].entries

    child = task.children[1].children[1]
    child.name = 'cc'
    assert 'cc_t1' in ed.nodes['root/comp1'].entries
    assert 'cc_t2' in ed.nodes['root/comp1'].entries
    assert 'comp2_t1' not in ed.nodes['root/comp1'].entries
    assert 'comp2_t2' not in ed.nodes['root/comp1'].entries

    child = task.children[1].children[1].children[0]
    child.add_access_exception('t', 2)
    assert 'simp3_t' in ed.nodes['root'].exceptions
    child.database_entries = {}
    assert not ed.nodes['root/comp1/cc'].entries
    assert 'simp2_t' not in ed.nodes['root'].exceptions


def test_handling_exceptions_modifications(task):
    """Test handling the possible modifictaion at the level of an exception.

    """
    ed = EditorModel(root=task)

    child = task.children[1].children[1].children[0]
    child.add_access_exception('t', 1)

    assert 'simp3_t' in ed.nodes['root/comp1'].exceptions
    assert 'simp3_t' in ed.nodes['root/comp1/comp2'].has_exceptions

    child.name = 'ss'
    assert 'ss_t' in ed.nodes['root/comp1'].exceptions
    assert 'ss_t' in ed.nodes['root/comp1/comp2'].has_exceptions

    parent = task.children[1]
    parent.name = 'cc'
    assert 'ss_t' in ed.nodes['root/cc'].exceptions
    assert 'ss_t' in ed.nodes['root/cc/comp2'].has_exceptions

    child.remove_access_exception('t')
    assert 'ss_t' not in ed.nodes['root/cc'].exceptions
    assert 'ss_t' not in ed.nodes['root/cc/comp2'].has_exceptions

    # For coverage try removing all exceptions.
    task.database.remove_access_exception('root/cc')


def test_handling_node_manipulation(task):
    """Test handling manipulation occuring on a node.

    """
    ed = EditorModel(root=task)

    cc = ComplexTask(name='cc')
    task.add_child_task(0, cc)
    assert 'root/cc' in ed.nodes
    assert cc is ed.nodes['root'].children[0].task

    task.remove_child_task(0)
    assert 'root/cc' not in ed.nodes

    # For coverage check that we could handle a list of changes
    ed._react_to_nodes([('', '', '')])

    # Test failing to find a task by path
    with pytest.raises(ValueError):
        ed._get_task('root/unknown')


def test_editor_widget(windows, task, dialog_sleep):
    """That the interaction with the editor widget makes sense.

    """
    dialog_sleep = dialog_sleep or 1

    def get_task_widget(editor):
        return editor.page_widget().widgets()[0].scroll_widget()

    def get_menu(task_widget, widget_index):
        flow_area = task_widget.widgets()[0]
        flow_item = flow_area.flow_items()[widget_index]
        menu = flow_item.flow_widget().widgets()[0].children[0]
        return menu

    task_with_exs = task.children[1].children[1].children[0]

    editor = DatabaseAccessEditor(declaration=Editor(id='ecpy.database'),
                                  selected_task=task)
    window = PageTestingWindow(widget=editor)
    window.show()
    process_app_events()
    sleep(dialog_sleep)

    r_widget = get_task_widget(editor)
    flow_area = r_widget.children[0]
    # Check that there is no contextual menu attached.
    assert len(flow_area.children[0].children[0].children) == 1

    # Add an access exception to the lowest level.
    editor.selected_task = task.children[1].children[1]
    process_app_events()
    sleep(dialog_sleep)

    widget = get_task_widget(editor)
    add_ex_action = get_menu(widget, 0).items()[0]
    add_ex_action.triggered = True
    process_app_events()
    assert task_with_exs.access_exs['t'] == 1
    sleep(dialog_sleep)

    # Move the exception up
    editor.selected_task = task.children[1]
    process_app_events()
    assert len(flow_area.flow_items()) == 4
    sleep(dialog_sleep)

    widget = get_task_widget(editor)
    flow_area = widget.children[0]
    menu = get_menu(widget, -1)
    assert len(menu.items()) == 2  # Check that both actions are there.
    move_up_action = menu.items()[0]
    move_up_action.triggered = True
    process_app_events()
    assert task_with_exs.access_exs['t'] == 2
    sleep(dialog_sleep)

    # Move the exception down
    editor.selected_task = task
    process_app_events()
    assert len(flow_area.flow_items()) == 3
    sleep(dialog_sleep)

    widget = get_task_widget(editor)
    flow_area = widget.children[0]
    menu = get_menu(widget, -1)
    assert len(menu.items()) == 1  # Check that only one action is there.
    move_down_action = menu.items()[0]
    move_down_action.triggered = True
    process_app_events()
    assert task_with_exs.access_exs['t'] == 1
    sleep(dialog_sleep)

    # Move the exception down (it disappears)
    editor.selected_task = task.children[1]
    process_app_events()
    sleep(dialog_sleep)

    widget = get_task_widget(editor)
    flow_area = widget.children[0]
    assert len(flow_area.flow_items()) == 4

    menu = get_menu(widget, -1)
    move_down_action = menu.items()[1]
    move_down_action.triggered = True
    process_app_events()
    assert not task_with_exs.access_exs
    sleep(dialog_sleep)

    editor.selected_task = task
    process_app_events()
    sleep(dialog_sleep)
