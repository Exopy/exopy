# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the functionality of task and interfaces declarators.

"""
import sys

import pytest
import enaml
from atom.api import Atom, Dict, List

from exopy.tasks.infos import TaskInfos, InterfaceInfos
from exopy.tasks.declarations import Task, Tasks, Interface, TaskConfig


class _DummyCollector(Atom):

    contributions = Dict()

    _delayed = List()


@pytest.fixture
def collector():
    return _DummyCollector()


# =============================================================================
# --- Test tasks --------------------------------------------------------------
# =============================================================================

@pytest.fixture
def task_decl():
    return Task(task='exopy.tasks.tasks.base_tasks:RootTask',
                view='exopy.tasks.tasks.base_views:RootTaskView')


def test_register_task_decl1(collector, task_decl):
    """Test registering the root task.

    """
    parent = Tasks(group='test', path='exopy.tasks.tasks')
    parent.insert_children(None, [task_decl])
    task_decl.task = 'base_tasks:RootTask'
    task_decl.view = 'base_views:RootTaskView'
    parent.register(collector, {})
    infos = collector.contributions['exopy.RootTask']
    from exopy.tasks.tasks.base_tasks import RootTask
    with enaml.imports():
        from exopy.tasks.tasks.base_views import RootTaskView
    assert infos.cls is RootTask
    assert infos.view is RootTaskView
    assert infos.metadata['group'] == 'test'


def test_regsitering_a_task_with_instruments(collector, task_decl):
    """Test registering a task supporting instruments.

    """
    parent = Tasks(group='test', path='exopy.tasks.tasks')
    parent.insert_children(None, [task_decl])
    task_decl.task = 'base_tasks:RootTask'
    task_decl.view = 'base_views:RootTaskView'
    task_decl.dependencies = ['dummy.dep']
    task_decl.instruments = ['DummyInstrument']
    parent.register(collector, {})
    infos = collector.contributions['exopy.RootTask']
    assert len(infos.dependencies) == 3


def test_register_task_decl_extend1(collector, task_decl):
    """Test extending a task.

    """
    collector.contributions['exopy.Task'] = TaskInfos()
    task_decl.task = 'exopy.Task'
    task_decl.instruments = ['test']
    task_decl.dependencies = ['dep']
    task_decl.register(collector, {})
    infos = collector.contributions['exopy.Task']
    assert infos.instruments == set(['test'])
    assert infos.dependencies == set(['dep'])


def test_register_task_decl_extend2(collector, task_decl):
    """Test extending a yet to be defined task.

    """
    task_decl.task = 'exopy.Task'
    task_decl.register(collector, {})
    assert collector._delayed == [task_decl]


def test_register_task_decl_extend3(collector, task_decl):
    """Test extending a task using wrong children.

    """
    tb = {}
    collector.contributions['exopy.Task'] = TaskInfos()
    task_decl.task = 'exopy.Task'
    task_decl.insert_children(None, [Task()])
    task_decl.register(collector, tb)
    assert 'exopy.Task' in tb


def test_register_task_decl_path_1(collector, task_decl):
    """Test handling wrong path : missing ':'.

    Such an errors can't be detected till the pass on the delayed and the
    dead-end is detected.

    """
    tb = {}
    task_decl.task = 'exopy.tasks'
    task_decl.register(collector, tb)
    assert task_decl in collector._delayed


def test_register_task_decl_path2(collector, task_decl):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    task_decl.view = 'exopy.tasks:tasks:Task'
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb


def test_register_task_decl_duplicate1(collector, task_decl):
    """Test handling duplicate : in collector.

    """
    collector.contributions['exopy.Task'] = None
    tb = {}
    task_decl.task = 'exopy.tasks:Task'
    task_decl.register(collector, tb)
    assert 'exopy.Task_duplicate1' in tb


def test_register_task_decl_duplicate2(collector, task_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'exopy.Task': 'rr'}
    task_decl.task = 'exopy.tasks:Task'
    task_decl.register(collector, tb)
    assert 'exopy.Task_duplicate1' in tb


def test_register_task_decl_taskcls1(collector, task_decl):
    """Test handling task class issues : failed import no such module.

    """
    tb = {}
    task_decl.task = 'exopy.tasks.foo:Task'
    task_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'import' in tb['exopy.Task']


def test_register_task_decl_taskcls1_bis(collector, task_decl):
    """Test handling task class issues : failed import error while importing.

    """
    tb = {}
    task_decl.task = 'exopy.testing.broken_module:Task'
    task_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'NameError' in tb['exopy.Task']


def test_register_task_decl_taskcls2(collector, task_decl):
    """Test handling task class issues : undefined in module.

    """
    tb = {}
    task_decl.task = 'exopy.tasks.tasks.base_tasks:Task'
    task_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'attribute' in tb['exopy.Task']


def test_register_task_decl_taskcls3(collector, task_decl):
    """Test handling task class issues : wrong type.

    """
    tb = {}
    task_decl.task = 'exopy.tasks.tasks.database:TaskDatabase'
    task_decl.register(collector, tb)
    assert ('exopy.TaskDatabase' in tb and
            'subclass' in tb['exopy.TaskDatabase'])


def test_register_task_decl_view1(collector, task_decl):
    """Test handling view issues : failed import no such module.

    """
    tb = {}
    task_decl.view = 'exopy.tasks.foo:Task'
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb and 'import' in tb['exopy.RootTask']


def test_register_task_decl_view1_bis(collector, task_decl):
    """Test handling view issues : failed import error while importing.

    """
    tb = {}
    task_decl.view = 'exopy.testing.broken_enaml:Task'
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb
    assert ('AttributeError' in tb['exopy.RootTask'] or
            'NameError' in tb['exopy.RootTask'])


def test_register_task_decl_view2(collector, task_decl):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    task_decl.view = 'exopy.tasks.tasks.base_views:Task'
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb and 'import' in tb['exopy.RootTask']


def test_register_task_decl_view3(collector, task_decl):
    """Test handling view issues : wrong type.

    """
    tb = {}
    task_decl.view = 'exopy.tasks.tasks.database:TaskDatabase'
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb and 'subclass' in tb['exopy.RootTask']


def test_register_task_decl_children(collector, task_decl):
    """Test handling child type issue.

    """
    tb = {}
    task_decl.insert_children(0, [Task()])
    task_decl.register(collector, tb)
    assert 'exopy.RootTask' in tb and 'Interface' in tb['exopy.RootTask']


def test_unregister_task_decl1(collector, task_decl):
    """Test unregistering a task.

    """
    task_decl.register(collector, {})
    task_decl.unregister(collector)
    assert not collector.contributions


def test_unregister_task_decl2(collector, task_decl):
    """Test unregistering a task which already disappeared.

    """
    task_decl.register(collector, {})
    collector.contributions = {}
    task_decl.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_unregister_task_decl3(collector, task_decl):
    """Test unregistering a task simply contributing instruments.

    """
    collector.contributions['exopy.Task'] = TaskInfos()
    task_decl.task = 'Task'
    task_decl.instruments = ['test']
    task_decl.dependencies = ['dep']
    task_decl.register(collector, {})
    task_decl.unregister(collector)
    assert not collector.contributions['exopy.Task'].instruments
    assert not collector.contributions['exopy.Task'].dependencies


def test_unregister_task_decl4(collector, task_decl):
    """Test unregistering a task which still have declared interfaces.

    """
    task_decl.register(collector, {})
    infos = collector.contributions['exopy.RootTask']
    i = InterfaceInfos(parent=infos)
    infos.interfaces['i'] = i
    task_decl.unregister(collector)
    assert not collector.contributions
    assert not i.parent


def test_str_task(task_decl):
    """Test string representation.

    """
    str(task_decl)


# =============================================================================
# --- Test interfaces ---------------------------------------------------------
# =============================================================================

@pytest.fixture
def int_decl():
    tasks = Tasks(path='exopy.tasks.tasks.logic')
    task = Task(task='loop_task:LoopTask', view='views.loop_view:LoopView')
    tasks.insert_children(None, [task])
    i = Interface(interface='loop_iterable_interface:IterableLoopInterface',
                  views=['views.loop_iterable_view:IterableLoopLabel'])
    task.insert_children(None, [i])
    return task, i


def test_interface_decl1(int_decl, collector):
    """Test registering an interface with a single view.

    """
    task, interface = int_decl
    task.register(collector, {})

    task_infos = list(collector.contributions.values())[0]
    assert len(task_infos.interfaces) == 1
    assert list(task_infos.interfaces.values())[0].parent is task_infos


def test_interface_decl2(int_decl, collector):
    """Test registering an interface with multiple views.

    """
    task, interface = int_decl
    interface.views = ['views.loop_iterable_view:IterableLoopLabel',
                       'views.loop_iterable_view:IterableLoopField']
    task.register(collector, {})
    contribs = list(collector.contributions.values())
    interfaces = list(contribs[0].interfaces.values())
    assert len(interfaces[0].views) == 2


def test_interface_decl3(int_decl, collector):
    """Test registering an interface with no view.

    """
    task, interface = int_decl
    interface.views = []
    task.register(collector, {})

    task_infos = list(collector.contributions.values())[0]
    assert len(task_infos.interfaces) == 1
    interface = list(task_infos.interfaces.values())[0]
    assert interface.parent is task_infos
    assert len(interface.views) == 0


def test_interface_decl4(collector, int_decl):
    """Test handling not yet registered task.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo'
    i.register(collector, tb)
    assert collector._delayed


def test_register_interface_extend_interface1(collector, int_decl):
    """Test extending an interface.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    collector.contributions['exopy.Task'] = infos

    task, interface = int_decl
    task.task = 'exopy.Task'
    interface.interface = 'Test'
    interface.instruments = ['test']
    interface.dependencies = ['dep']

    task.register(collector, {})
    interface = collector.contributions['exopy.Task'].interfaces['Test']
    assert interface.instruments == {'test'}
    assert 'dep' in interface.dependencies
    assert len(interface.dependencies) == 3


def test_register_interface_extend_interface2(collector, int_decl):
    """Test extending an interface not yet declared.

    """
    collector.contributions['exopy.Task'] = TaskInfos()

    task, interface = int_decl
    task.task = 'exopy.Task'
    interface.interface = 'Test'
    interface.instruments = ['test']

    task.register(collector, {})
    assert collector._delayed == [interface]


def test_register_interface_extend_task(collector, int_decl):
    """Test extending a task by adding interfaces.

    """
    collector.contributions['exopy.Task'] = TaskInfos()
    task, _ = int_decl
    task.task = 'exopy.Task'
    task.register(collector, {})
    assert collector.contributions['exopy.Task'].interfaces


def test_register_interface_decl_missing_ext(collector):
    """Test handling missing extended, no parent.

    """
    tb = {}
    Interface(interface='foo:bar').register(collector, tb)
    assert 'task/interface ' in tb['foo:bar']


def test_register_interface_decl_path_1(int_decl, collector):
    """Test handling wrong path : missing ':'.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo.tt'
    task.register(collector, tb)
    assert 'exopy.LoopTask:foo.tt'


def test_register_interface_decl_path2(int_decl, collector):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    task, i = int_decl
    i.views = 'foo:bar:foo'
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface' in tb


def test_register_interface_decl_duplicate1(int_decl, collector):
    """Test handling duplicate : in collector.

    """
    tb = {}
    task, i = int_decl
    infos = TaskInfos(interfaces={'exopy.IterableLoopInterface': None})
    collector.contributions[task.id] = infos
    i.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface_duplicate1' in tb


def test_register_interface_decl_duplicate2(int_decl, collector):
    """Test handling duplicate : in traceback.

    """
    tb = {'exopy.LoopTask:exopy.IterableLoopInterface': ''}
    task, i = int_decl
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface_duplicate1' in tb


def test_register_interface_decl_cls1(int_decl, collector):
    """Test handling interface class issues : failed import wrong path.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'foo.bar:baz'
    task.register(collector, tb)
    err_name = ('ImportError' if sys.version_info < (3, 6) else
                'ModuleNotFoundError')
    assert ('exopy.LoopTask:exopy.baz' in tb and
            err_name in tb['exopy.LoopTask:exopy.baz'])


def test_register_interface_decl_cls1_bis(collector):
    """Test handling interface class issues : failed import Name error.

    """
    tb = {}
    task = Task(task='exopy.tasks.tasks.logic.loop_task:LoopTask',
                view='exopy.tasks.tasks.logic.views.loop_view:LoopView')
    i = Interface(interface='loop_iterable_interface:IterableLoopInterface',
                  views=['views.loop_iterable_view:IterableLoopLabel'])
    task.insert_children(None, [i])
    i.interface = 'exopy.testing.broken_module:Test'
    task.register(collector, tb)
    assert ('exopy.LoopTask:exopy.Test' in tb and
            'NameError' in tb['exopy.LoopTask:exopy.Test'])


def test_register_interface_decl_cls2(int_decl, collector):
    """Test handling interface class issues : undefined in module.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'loop_iterable_interface:baz'
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.baz' in tb


def test_register_interface_decl_cls3(collector, int_decl):
    """Test handling interface class issues : wrong type.

    """
    tb = {}
    task, i = int_decl
    i.interface = 'loop_task:LoopTask'
    task.register(collector, tb)
    assert ('exopy.LoopTask:exopy.LoopTask' in tb and
            'subclass' in tb['exopy.LoopTask:exopy.LoopTask'])


def test_register_interface_decl_view1(int_decl, collector):
    """Test handling view issues : failed import due to wrong path.

    """
    tb = {}
    task, i = int_decl
    i.views = 'foo.bar:baz'
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface' in tb


def test_register_interface_decl_view1_bis(int_decl, collector):
    """Test handling view issues : failed import due to NameError.

    """
    tb = {}
    task = Task(task='exopy.tasks.tasks.logic.loop_task:LoopTask',
                view='exopy.tasks.tasks.logic.views.loop_view:LoopView')
    i = Interface(interface='exopy.tasks.tasks.logic.'
                            'loop_iterable_interface:IterableLoopInterface',
                  views=['_dumy__:Test', 'exopy.testing.broken_enaml:Task'])
    task.insert_children(None, [i])
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface_1' in tb
    assert ('AttributeError' in
            tb['exopy.LoopTask:exopy.IterableLoopInterface_1'] or
            'NameError' in tb['exopy.LoopTask:exopy.IterableLoopInterface_1'])


def test_register_interface_decl_view2(int_decl, collector):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    task, i = int_decl
    i.views = 'views.loop_iterable_view:baz'
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface' in tb


def test_register_interface_decl_children1(int_decl, collector):
    """Test handling child type issue.

    """
    tb = {}
    task, i = int_decl
    i.insert_children(None, [Task()])
    task.register(collector, tb)
    assert 'exopy.LoopTask:exopy.IterableLoopInterface' in tb and\
        'Interface' in tb['exopy.LoopTask:exopy.IterableLoopInterface']


def test_register_interface_decl_children2(int_decl, collector):
    """Test handling child type issue when extending.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    collector.contributions['exopy.Task'] = infos

    task, interface = int_decl
    task.task = 'exopy.Task'
    interface.interface = 'Test'
    interface.insert_children(None, [Task()])

    tb = {}
    task.register(collector, tb)
    assert ('exopy.Task:Test' in tb and
            'Interface' in tb['exopy.Task:Test'])


def test_unregister_interface_decl(int_decl, collector):
    """Test unregistering an interface.

    """
    task, i = int_decl
    task.register(collector, {})
    i.unregister(collector)
    assert not collector.contributions['exopy.LoopTask'].interfaces


def test_unregister_interface_decl_bis(int_decl, collector):
    """Test unregistering an task with an interface.

    """
    task, i = int_decl
    task.register(collector, {})
    task.unregister(collector)
    assert not collector.contributions


def test_unregister_interface_decl2(collector, int_decl):
    """Test unregistering an interface for a task which already disappeared.

    """
    task, i = int_decl
    task.register(collector, {})
    collector.contributions = {}
    i.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_unregister_interface_decl3(collector, int_decl):
    """Test unregistering an interface which already disappeared.

    """
    task, i = int_decl
    task.register(collector, {})
    collector.contributions['exopy.LoopTask'].interfaces = {}
    i.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_unregister_interface_decl4(collector, int_decl):
    """Test unregistering an interface simply contributing instruments.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos()
    collector.contributions['exopy.Task'] = infos

    task, interface = int_decl
    task.task = 'exopy.Task'
    interface.interface = 'Test'
    interface.instruments = ['test']
    interface.dependencies = ['dep']

    task.register(collector, {})
    interface = collector.contributions['exopy.Task'].interfaces['Test']
    assert interface.instruments == {'test'}
    task.unregister(collector)
    assert not interface.instruments
    assert not interface.dependencies


def test_unregister_interface_decl5(collector, int_decl):
    """Test unregistering an interface which still have declared interfaces.

    """
    task, i = int_decl
    task.register(collector, {})
    t_infos = collector.contributions['exopy.LoopTask']
    infos = list(t_infos.interfaces.values())[0]
    i = InterfaceInfos(parent=infos)
    infos.interfaces['i'] = i
    task.unregister(collector)
    assert not collector.contributions
    assert not i.parent


@pytest.fixture
def nested_int_decl(int_decl):
    task, interface = int_decl
    i = Interface(interface='loop_linspace_interface:LinspaceLoopInterface',
                  views=['views.loop_linspace_view:LinspaceLoopView'])
    interface.insert_children(None, [i])
    return task, i


# HINT this is part broken as the class is not a subclass of IInterface
def test_nested_interfaces_register(nested_int_decl, collector):
    """Test registering and unregistering an interface to an interface.

    """
    task, interface = nested_int_decl
    task.register(collector, {})

    interfaces = collector.contributions['exopy.LoopTask'].interfaces
    assert interfaces['exopy.IterableLoopInterface'].interfaces
    interface.parent.unregister(collector)


def test_nested_interfaces_extend1(nested_int_decl, collector):
    """Test registering, unregistering an interface extending an interface
    to an interface.

    """
    infos = TaskInfos()
    infos.interfaces['Test'] = InterfaceInfos(interfaces={'Nested':
                                                          InterfaceInfos()})
    collector.contributions['exopy.Task'] = infos

    task, interface = nested_int_decl
    task.task = 'exopy.Task'
    interface.parent.interface = 'Test'
    interface.interface = 'Nested'
    interface.instruments = ['test']

    task.register(collector, {})
    i = collector.contributions['exopy.Task'].interfaces['Test']
    assert i.interfaces['Nested'].instruments == {'test'}
    interface.parent.unregister(collector)


def test_str_interface(int_decl):
    str(int_decl[1])


# =============================================================================
# --- Test configs ------------------------------------------------------------
# =============================================================================

@pytest.fixture
def config_decl():
    class Config(TaskConfig):
        def get_task_class(self):
            from exopy.tasks.tasks.base_tasks import BaseTask
            return BaseTask

    return Config(
        config='exopy.tasks.configs.base_configs:PyTaskConfig',
        view='exopy.tasks.configs.base_config_views:PyConfigView')


def test_register_config_decl(collector, config_decl):
    """Test registering the root task.

    """
    config_decl.register(collector, {})
    from exopy.tasks.tasks.base_tasks import BaseTask
    infos = collector.contributions[BaseTask]
    from exopy.tasks.configs.base_configs import PyTaskConfig
    with enaml.imports():
        from exopy.tasks.configs.base_config_views import PyConfigView
    assert infos.cls is PyTaskConfig
    assert infos.view is PyConfigView


def test_register_config_fail_to_get_task(collector, config_decl):
    """Test handling wrong path : missing ':'.

    """
    tb = {}

    def dummy(self):
        raise Exception()
    type(config_decl).get_task_class = dummy
    config_decl.register(collector, tb)
    assert 'exopy.PyTaskConfig' in tb


def test_register_config_decl_path_1(collector, config_decl):
    """Test handling wrong path : missing ':'.

    """
    tb = {}
    config_decl.config = 'exopy.tasks'
    config_decl.register(collector, tb)
    assert 'exopy.tasks' in tb


def test_register_config_decl_path2(collector, config_decl):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    config_decl.view = 'exopy.tasks:tasks:Task'
    config_decl.register(collector, tb)
    assert 'exopy.PyTaskConfig' in tb


def test_register_config_decl_duplicate1(collector, config_decl):
    """Test handling duplicate config for a task.

    """
    from exopy.tasks.tasks.base_tasks import BaseTask
    collector.contributions[BaseTask] = None
    tb = {}
    config_decl.register(collector, tb)
    assert 'exopy.PyTaskConfig' in tb


def test_register_config_decl_duplicate2(collector, config_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'exopy.PyTaskConfig': 'rr'}
    config_decl.register(collector, tb)
    assert 'PyTaskConfig_duplicate1' in tb


def test_register_config_decl_cls1(collector, config_decl):
    """Test handling task class issues : failed import wrong path.

    """
    tb = {}
    config_decl.config = 'exopy.tasks.foo:Task'
    config_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'import' in tb['exopy.Task']


def test_register_config_decl_cls1_bis(collector, config_decl):
    """Test handling task class issues : failed import NameError.

    """
    tb = {}
    config_decl.config = 'exopy.testing.broken_module:Task'
    config_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'NameError' in tb['exopy.Task']


def test_register_task_decl_cls2(collector, config_decl):
    """Test handling task class issues : undefined in module.

    """
    tb = {}
    config_decl.config = 'exopy.tasks.tasks.base_tasks:Task'
    config_decl.register(collector, tb)
    assert 'exopy.Task' in tb and 'attribute' in tb['exopy.Task']


def test_register_task_decl_cls3(collector, config_decl):
    """Test handling task class issues : wrong type.

    """
    tb = {}
    config_decl.config = 'exopy.tasks.tasks.database:TaskDatabase'
    config_decl.register(collector, tb)
    assert ('exopy.TaskDatabase' in tb and
            'subclass' in tb['exopy.TaskDatabase'])


def test_register_config_decl_view1(collector, config_decl):
    """Test handling view issues : failed import wrong path.

    """
    tb = {}
    config_decl.view = 'exopy.tasks.foo:Task'
    config_decl.register(collector, tb)
    assert ('exopy.PyTaskConfig' in tb and
            'import' in tb['exopy.PyTaskConfig'])


def test_register_config_decl_view1bis(collector, config_decl):
    """Test handling view issues : failed import NameError.

    """
    tb = {}
    config_decl.view = 'exopy.testing.broken_module:Task'
    config_decl.register(collector, tb)
    assert ('exopy.PyTaskConfig' in tb and
            'NameError' in tb['exopy.PyTaskConfig'])


def test_register_config_decl_view2(collector, config_decl):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    config_decl.view = 'exopy.tasks.tasks.base_views:Task'
    config_decl.register(collector, tb)
    assert 'exopy.PyTaskConfig' in tb and 'import' in tb['exopy.PyTaskConfig']


def test_register_config_decl_view3(collector, config_decl):
    """Test handling view issues : wrong type.

    """
    tb = {}
    config_decl.view = 'exopy.tasks.tasks.database:TaskDatabase'
    config_decl.register(collector, tb)
    assert ('exopy.PyTaskConfig' in tb and
            'subclass' in tb['exopy.PyTaskConfig'])


def test_unregister_config_decl1(collector, config_decl):
    """Test unregistering a task.

    """
    config_decl.register(collector, {})
    config_decl.unregister(collector)
    assert not collector.contributions


def test_unregister_config_decl2(collector, config_decl):
    """Test unregistering a task which already disappeared.

    """
    config_decl.register(collector, {})
    collector.contributions = {}
    config_decl.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_str_config(config_decl):
    """Test string representation.

    """
    str(config_decl)
