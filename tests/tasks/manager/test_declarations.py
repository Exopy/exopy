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

from ecpy.tasks.manager.infos import TaskInfos, InterfaceInfos
from ecpy.tasks.manager.declarations import Task, Tasks, Interface


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


def test_register_task_decl_taskcls3(plugin, task_decl):
    """Test handling task class issues : wrong type.

    """
    tb = {}
    task_decl.task = 'ecpy.tasks.tools.database:TaskDatabase'
    task_decl.register(plugin, tb)
    assert 'TaskDatabase' in tb and 'subclass' in tb['TaskDatabase']


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


def test_register_task_decl_view3(plugin, task_decl):
    """Test handling view issues : wrong type.

    """
    tb = {}
    task_decl.view = 'ecpy.tasks.tools.database:TaskDatabase'
    task_decl.register(plugin, tb)
    assert 'RootTask' in tb and 'subclass' in tb['RootTask']


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
    # Would raise an error if the error was not properly catched.


def test_unregister_task_decl3(plugin, task_decl):
    """Test unregistering a task simply contributing instruments.

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
    tasks = Tasks(path='ecpy.tasks.tasks.logic')
    task = Task(task='loop_task:LoopTask', view='views.loop_view:LoopView')
    tasks.insert_children(None, [task])
    i = Interface(interface='loop_iterable_interface:IterableLoopInterface',
                  views=['views.loop_iterable_view:IterableLoopLabel'])
    task.insert_children(None, [i])
    return task, i


def test_interface_decl1(int_decl, plugin):
    """Test registering an interface with a single view.

    """
    task, interface = int_decl
    task.register(plugin, {})
    assert len(plugin._tasks.values()[0].interfaces) == 1


def test_interface_decl2(int_decl, plugin):
    """Test registering an interface with multiple views.

    """
    task, interface = int_decl
    interface.views = ['views.loop_iterable_view:IterableLoopLabel',
                       'views.loop_iterable_view:IterableLoopField']
    task.register(plugin, {})
    assert len(plugin._tasks.values()[0].interfaces.values()[0].views) == 2


def test_interface_decl3(plugin, int_decl):
    """Test handling not yet registered task.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo'
    i.register(plugin, tb)
    assert plugin._delayed


def test_register_interface_extend_interface1(plugin, int_decl):
    """Test extending an interface.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    plugin._tasks['Task'] = infos

    task, interface = int_decl
    task.task = 'Task'
    interface.interface = 'Test'
    interface.instruments = ['test']

    task.register(plugin, {})
    assert plugin._tasks['Task'].interfaces['Test'].instruments == {'test'}


def test_register_interface_extend_interface2(plugin, int_decl):
    """Test extending an interface not yet declared.

    """
    plugin._tasks['Task'] = TaskInfos()

    task, interface = int_decl
    task.task = 'Task'
    interface.interface = 'Test'
    interface.instruments = ['test']

    task.register(plugin, {})
    assert plugin._delayed == [interface]


def test_register_interface_extend_task(plugin, int_decl):
    """Test extending a task by adding interfaces.

    """
    plugin._tasks['Task'] = TaskInfos()
    task, _ = int_decl
    task.task = 'Task'
    task.register(plugin, {})
    assert plugin._tasks['Task'].interfaces


def test_register_interface_decl_missing_ext(plugin):
    """Test handling missing extended, no parent.

    """
    tb = {}
    Interface(interface='foo:bar').register(plugin, tb)
    assert 'task/interface ' in tb['bar']


def test_register_interface_decl_path_1(int_decl, plugin):
    """Test handling wrong path : missing ':'.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo.tt'
    task.register(plugin, tb)
    assert 'Error 0' in tb


def test_register_interface_decl_path2(int_decl, plugin):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    task, i = int_decl
    i.views = 'foo:bar:foo'
    task.register(plugin, tb)
    assert 'IterableLoopInterface' in tb


def test_register_interface_decl_duplicate1(int_decl, plugin):
    """Test handling duplicate : in plugin.

    """
    tb = {}
    task, i = int_decl
    infos = TaskInfos(interfaces={i.interface.split(':')[-1]: None})
    plugin._tasks[task.task.split(':')[-1]] = infos
    i.register(plugin, tb)
    assert 'IterableLoopInterface_duplicate1' in tb


def test_register_interface_decl_duplicate2(int_decl, plugin):
    """Test handling duplicate : in traceback.

    """
    tb = {'IterableLoopInterface': ''}
    task, i = int_decl
    task.register(plugin, tb)
    assert 'IterableLoopInterface_duplicate1' in tb


def test_register_interface_decl_cls1(int_decl, plugin):
    """Test handling interface class issues : failed import.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo.bar:baz'
    task.register(plugin, tb)
    assert 'baz' in tb


def test_register_interface_decl_cls2(int_decl, plugin):
    """Test handling interface class issues : undefined in module.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'loop_iterable_interface:baz'
    task.register(plugin, tb)
    assert 'baz' in tb


def test_register_interface_decl_cls3(plugin, int_decl):
    """Test handling interface class issues : wrong type.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'loop_task:LoopTask'
    task.register(plugin, tb)
    assert 'LoopTask' in tb and 'subclass' in tb['LoopTask']


def test_register_interface_decl_view1(int_decl, plugin):
    """Test handling view issues : failed import.

    """
    tb = {}
    task, i = int_decl
    i.views = 'foo.bar:baz'
    task.register(plugin, tb)
    assert 'IterableLoopInterface' in tb


def test_register_interface_decl_view2(int_decl, plugin):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    task, i = int_decl
    i.views = 'views.loop_iterable_view:baz'
    task.register(plugin, tb)
    assert 'IterableLoopInterface' in tb


def test_register_interface_decl_children1(int_decl, plugin):
    """Test handling child type issue.

    """
    tb = {}
    task, i = int_decl
    i.insert_children(None, [Task()])
    task.register(plugin, tb)
    assert 'IterableLoopInterface' in tb and\
        'Interface' in tb['IterableLoopInterface']


def test_register_interface_decl_children2(int_decl, plugin):
    """Test handling child type issue when extending.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    plugin._tasks['Task'] = infos

    task, interface = int_decl
    task.task = 'Task'
    interface.interface = 'Test'
    interface.insert_children(None, [Task()])

    tb = {}
    task.register(plugin, tb)
    assert 'Test' in tb and\
        'Interface' in tb['Test']


def test_unregister_interface_decl(int_decl, plugin):
    """Test unregistering an interface.

    """
    task, i = int_decl
    task.register(plugin, {})
    i.unregister(plugin)
    assert not plugin._tasks['LoopTask'].interfaces


def test_unregister_interface_decl_bis(int_decl, plugin):
    """Test unregistering an task with an interface.

    """
    task, i = int_decl
    task.register(plugin, {})
    task.unregister(plugin)
    assert not plugin._tasks


def test_unregister_interface_decl2(plugin, int_decl):
    """Test unregistering an interface for a task which already disappeared.

    """
    task, i = int_decl
    task.register(plugin, {})
    plugin._tasks = {}
    i.unregister(plugin)
    # Would raise an error if the error was not properly catched.


def test_unregister_interface_decl3(plugin, int_decl):
    """Test unregistering an interface which already disappeared.

    """
    task, i = int_decl
    task.register(plugin, {})
    plugin._tasks['LoopTask'].interfaces = {}
    i.unregister(plugin)
    # Would raise an error if the error was not properly catched.


def test_unregister_interface_decl4(plugin, int_decl):
    """Test unregistering an interface simply contributing instruments.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    plugin._tasks['Task'] = infos

    task, interface = int_decl
    task.task = 'Task'
    interface.interface = 'Test'
    interface.instruments = ['test']

    task.register(plugin, {})
    assert plugin._tasks['Task'].interfaces['Test'].instruments == {'test'}
    task.unregister(plugin)
    assert not plugin._tasks['Task'].interfaces['Test'].instruments


@pytest.fixture
def nested_int_decl(int_decl):
    task, interface = int_decl
    i = Interface(interface='loop_linspace_interface:LinspaceLoopInterface',
                  views=['views.loop_linspace_view:LinspaceLoopView'])
    interface.insert_children(None, [i])
    return task, i


def test_nested_interfaces_register(nested_int_decl, plugin):
    """Test registering and unregistering an interface to an interface.

    """
    task, interface = nested_int_decl
    task.register(plugin, {})

    interfaces = plugin._tasks['LoopTask'].interfaces
    assert interfaces['IterableLoopInterface'].interfaces
    interface.parent.unregister(plugin)


def test_nested_interfaces_extend1(nested_int_decl, plugin):
    """Test registering, unregistering an interface extending an interface
    to an interface.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos(interfaces={'Nested':
                                                          InterfaceInfos()})
    plugin._tasks['Task'] = infos

    task, interface = nested_int_decl
    task.task = 'Task'
    interface.parent.interface = 'Test'
    interface.interface = 'Nested'
    interface.instruments = ['test']

    task.register(plugin, {})
    interfaces = plugin._tasks['Task'].interfaces['Test'].interfaces
    assert interfaces['Nested'].instruments == {'test'}
    interface.parent.unregister(plugin)
