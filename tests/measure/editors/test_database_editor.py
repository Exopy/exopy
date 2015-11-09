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
     EditorModel, NodeModel

from ...util import process_app_events

with enaml.imports():
    from ecpy.measure.editors.database_access_editor import\
        DatabaseAccessEditor
    from .testing_window import EditorTestingWindow


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


def test_editor_modifying_exception_level(task):
    """Test modifying the level of an access exception.

    """
    ed = EditorModel(root=task)
    rnode = ed.nodes['root']

    node = rnode.children[0].children[0]
    node.add_exception('simp3_t')
    assert 'simp3_t' in node.parent.exceptions

    ed.increase_exc_level('root/comp1', 'simp3_t')
    assert 'simp3_t' not in node.parent.exceptions
    assert 'simp3_t' in node.parent.parent.exceptions

    ed.decrease_exc_level('root', 'simp3_t')
    assert 'simp3_t' in node.parent.exceptions
    assert 'simp3_t' not in node.parent.parent.exceptions

    ed.decrease_exc_level('root/comp1', 'simp3_t')
    assert 'simp3_t' not in node.parent.exceptions


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

    child.name = 'ss'
    assert 'ss_t' in ed.nodes['root/comp1'].exceptions

    parent = task.children[1]
    parent.name = 'cc'
    assert 'ss_t' in ed.nodes['root/cc'].exceptions

    child.remove_access_exception('t')
    assert 'ss_t' not in ed.nodes['root/cc'].exceptions


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


def test_editor_widget():
    pass
