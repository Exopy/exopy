# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the functionality of task and interfaces declarators.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from atom.api import Atom, Dict, List

from ecpy.tasks.manager.infos import TaskInfos
from ecpy.tasks.manager.declarations import Task, Tasks, Interface, Interfaces


class _DummyPLugin(Atom):

    _tasks = Dict()

    _delayed = List()


@pytest.fixture
def plugin():
    return _DummyPLugin()


# =============================================================================
# --- Test tasks --------------------------------------------------------------
# =============================================================================

@pytest.fixture
def task_decl():
    return Task(task='ecpy.tasks.base_tasks:RootTask',
                view='ecpy.tasks.base_views:RootTaskView')


def test_register_task_decl1(plugin, task_decl):
    """Test registering the root task.

    """
    parent = Tasks(group='test', path='ecpy.tasks')
    parent.insert_children(None, [task_decl])
    task_decl.task = 'base_tasks:RootTask'
    task_decl.view = 'base_views:RootTaskView'
    parent.register(plugin, {})
    infos = plugin._tasks['RootTask']
    from ecpy.tasks.base_tasks import RootTask
    with enaml.imports():
        from ecpy.tasks.base_views import RootTaskView
    assert infos.cls is RootTask
    assert infos.view is RootTaskView
    assert infos.metadata['group'] == 'test'


def test_register_task_decl_extend1(plugin, task_decl):
    """Test extending a task.

    """
    plugin._tasks['Task'] = TaskInfos()
    task_decl.task = 'Task'
    task_decl.instruments = ['test']
    task_decl.register(plugin, {})
    assert plugin._tasks['Task'].instruments == set(['test'])


def test_register_task_decl_extend2(plugin, task_decl):
    """Test extending a task by adding interfaces.

    """
    # XXXX
    pass


def test_register_task_decl_extend3(plugin, task_decl):
    """Test extending a yet to be defined task.

    """
    task_decl.task = 'Task'
    task_decl.register(plugin, {})
    assert plugin._delayed == [task_decl]


def test_register_task_decl_extend4(plugin, task_decl):
    """Test extending a task using wrong children.

    """
    tb = {}
    plugin._tasks['Task'] = TaskInfos()
    task_decl.task = 'Task'
    task_decl.insert_children(None, [Task()])
    task_decl.register(plugin, tb)
    assert 'Task' in tb['Task']


def test_register_task_decl_path_1(plugin, task_decl):
    """Test handling wrong path : missing ':'.

    """
    tb = {}
    task_decl.task = 'ecpy.tasks'
    task_decl.register(plugin, tb)
    assert 'Error 0' in tb


def test_register_task_decl_path2(plugin, task_decl):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    task_decl.view = 'ecpy.tasks:tasks:Task'
    task_decl.register(plugin, tb)
    assert 'RootTask' in tb


def test_register_task_decl_duplicate1(plugin, task_decl):
    """Test handling duplicate : in plugin.

    """
    plugin._tasks['Task'] = None
    tb = {}
    task_decl.task = 'ecpy.tasks:Task'
    task_decl.register(plugin, tb)
    assert 'Task_duplicate1' in tb


def test_register_task_decl_duplicate2(plugin, task_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'Task': 'rr'}
    task_decl.task = 'ecpy.tasks:Task'
    task_decl.register(plugin, tb)
    assert 'Task_duplicate1' in tb


def test_register_task_decl_taskcls1(plugin, task_decl):
    """Test handling task class issues : failed import.

    """
    tb = {}
    task_decl.task = 'ecpy.tasks.foo:Task'
    task_decl.register(plugin, tb)
    assert 'Task' in tb and 'import' in tb['Task']


def test_register_task_decl_taskcls2(plugin, task_decl):
    """Test handling task class issues : undefined in module.

    """
    tb = {}
    task_decl.task = 'ecpy.tasks.base_tasks:Task'
    task_decl.register(plugin, tb)
    assert 'Task' in tb and 'attribute' in tb['Task']


def test_register_task_decl_view1(plugin, task_decl):
    """Test handling view issues : failed import.

    """
    tb = {}
    task_decl.view = 'ecpy.tasks.foo:Task'
    task_decl.register(plugin, tb)
    assert 'RootTask' in tb and 'import' in tb['RootTask']


def test_register_task_decl_view2(plugin, task_decl):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    task_decl.view = 'ecpy.tasks.base_views:Task'
    task_decl.register(plugin, tb)
    assert 'RootTask' in tb and 'import' in tb['RootTask']


def test_register_task_decl_children(plugin, task_decl):
    """Test handling child type issue.

    """
    tb = {}
    task_decl.insert_children(0, [Task()])
    task_decl.register(plugin, tb)
    assert 'RootTask' in tb and 'Interface' in tb['RootTask']


def test_unregister_task_decl1(plugin, task_decl):
    """Test unregistering a task.

    """
    task_decl.register(plugin, {})
    task_decl.unregister(plugin)
    assert not plugin._tasks


def test_unregister_task_decl2(plugin, task_decl):
    """Test unregistering a task which already disappeared.

    """
    task_decl.register(plugin, {})
    plugin._tasks = {}
    task_decl.unregister(plugin)
    assert not plugin._tasks


def test_unregister_task_decl3(plugin, task_decl):
    """Test unregistering a task simply contributing drivers.

    """
    plugin._tasks['Task'] = TaskInfos()
    task_decl.task = 'Task'
    task_decl.instruments = ['test']
    task_decl.register(plugin, {})
    task_decl.unregister(plugin)
    assert not plugin._tasks['Task'].instruments


# =============================================================================
# --- Test interfaces ---------------------------------------------------------
# =============================================================================

@pytest.fixture
def int_decl():
    return Interface(interface='ecpy.tasks.base_tasks:RootTask',
                     views='ecpy.tasks.base_views:RootTaskView')


def test_interface_decl1():
    """
    """
    pass


def test_interface_decl_missing_ext():
    """Test handling missing extended, no parent.

    """
    pass


def test_interface_decl_path_1():
    """Test handling wrong path : missing ':'.

    """
    pass


def test_interface_decl_path2():
    """Test handling wrong path : too many ':'.

    """
    pass


def test_interface_decl_duplicate1():
    """Test handling duplicate : in plugin.

    """
    pass


def test_interface_decl_duplicate2():
    """Test handling duplicate : in traceback.

    """
    pass


def test_interface_decl_cls1():
    """Test handling task class issues : failed import.

    """
    pass


def test_interface_decl_cls2():
    """Test handling task class issues : undefined in module.

    """
    pass


def test_interface_decl_view1():
    """Test handling view issues : failed import.

    """
    pass


def test_interface_decl_view2():
    """Test handling view issues : undefined in module.

    """
    pass


def test_interface_decl_children():
    """Test handling child type issue.

    """
    pass


def test_unregister_interface_decl():
    """
    """
    pass
