# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test dependency collection functions.

"""
from operator import getitem

import pytest

from exopy.app.dependencies.api import (BuildDependency,
                                        RuntimeDependencyAnalyser)
from exopy.tasks.api import ComplexTask, InstrumentTask, TaskInterface
from exopy.tasks.infos import (TaskInfos, InterfaceInfos,
                               INSTR_RUNTIME_TASK_DRIVERS_ID,
                               INSTR_RUNTIME_TASK_PROFILES_ID,
                               INSTR_RUNTIME_INTERFACE_DRIVERS_ID,
                               INSTR_RUNTIME_INTERFACE_PROFILES_ID)


@pytest.fixture
def task_dep_collector(task_workbench):
    """Collector for task dependencies.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'build_deps'][0]
    return [b for b in dep_ext.get_children(BuildDependency)
            if b.id == 'exopy.task'][0]


@pytest.fixture
def interface_dep_collector(task_workbench):
    """Collector for interface dependencies.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'build_deps'][0]
    return [b for b in dep_ext.get_children(BuildDependency)
            if b.id == 'exopy.tasks.interface'][0]


@pytest.fixture
def driver_dep_collector(task_workbench):
    """Collector for driver dependencies for task supporting instrument and
    having the proper selected_intrument member.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == INSTR_RUNTIME_TASK_DRIVERS_ID][0]


@pytest.fixture
def profile_dep_collector(task_workbench):
    """Collector for profile dependencies for task supporting instrument and
    having the proper selected_intrument member.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == INSTR_RUNTIME_TASK_PROFILES_ID][0]


@pytest.fixture
def i_driver_dep_collector(task_workbench):
    """Collector for driver dependencies for interface supporting instrument
    and having the proper selected_intrument member or being attached to a task
    that does.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == INSTR_RUNTIME_INTERFACE_DRIVERS_ID][0]


@pytest.fixture
def i_profile_dep_collector(task_workbench):
    """Collector for profile dependencies for interface supporting instrument
    and having the proper selected_intrument member or being attached to a task
    that does.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == INSTR_RUNTIME_INTERFACE_PROFILES_ID][0]


def test_analysing_task_dependencies(monkeypatch, task_workbench,
                                     task_dep_collector):
    """Test analysing the dependencies of a task.

    """
    runtime = {'test'}
    plugin = task_workbench.get_plugin('exopy.tasks')
    monkeypatch.setattr(plugin.get_task_infos('exopy.ComplexTask'),
                        'dependencies', runtime)

    dep = set()
    errors = dict()
    run = task_dep_collector.analyse(task_workbench, ComplexTask(), getattr,
                                     dep, errors)

    assert run == runtime
    assert 'exopy.ComplexTask' in dep
    assert not errors

    dep = set()
    run = task_dep_collector.analyse(task_workbench, {'task_id': '__dummy__'},
                                     getitem, dep, errors)
    assert not run
    assert not dep
    assert '__dummy__' in errors


def test_validating_task_dependencies(task_workbench, task_dep_collector):
    """Test validating task dependencies.

    """
    errors = {}
    task_dep_collector.validate(task_workbench,
                                {'exopy.ComplexTask', '__dummy__'}, errors)
    assert 'exopy.ComplexTask' not in errors
    assert '__dummy__' in errors


def test_collecting_task_dependencies(task_workbench, task_dep_collector):
    """Test collecting the dependencies found in a task.

    """
    dependencies = dict.fromkeys(['exopy.ComplexTask', '__dummy__'])
    errors = {}
    task_dep_collector.collect(task_workbench, dependencies, errors)
    assert 'exopy.ComplexTask' in dependencies
    assert '__dummy__' in errors


def test_analysing_interface_dependencies(monkeypatch, task_workbench,
                                          interface_dep_collector):
    """Test analysing the dependencies in an interface.

    """
    runtime = {'test'}
    interface = 'exopy.LoopTask:exopy.LinspaceLoopInterface'
    plugin = task_workbench.get_plugin('exopy.tasks')
    monkeypatch.setattr(plugin.get_interface_infos(interface), 'dependencies',
                        runtime)

    dep = set()
    errors = dict()
    run = interface_dep_collector.analyse(task_workbench,
                                          {'interface_id': str(interface)},
                                          getitem, dep, errors)

    assert run == runtime
    assert interface in dep
    assert not errors

    dep.clear()
    run = interface_dep_collector.analyse(task_workbench,
                                          {'interface_id':
                                              'LoopTask:__dummy__'},
                                          getitem, dep, errors)
    assert not run
    assert not dep
    assert 'LoopTask:__dummy__' in errors


def test_validating_interface_dependencies(task_workbench,
                                           interface_dep_collector):
    """Test validating interface dependencies.

    """
    errors = {}
    interface_dep_collector.validate(
        task_workbench,
        {'exopy.LoopTask:exopy.LinspaceLoopInterface',
         'LoopTask:__dummy__'}, errors)
    assert 'exopy.LoopTask:exopy.LinspaceLoopInterface' not in errors
    assert 'LoopTask:__dummy__' in errors


def test_collecting_interface_dependencies(task_workbench,
                                           interface_dep_collector):
    """Test collecting the dependencies found in an interface.

    """
    dependencies = dict.fromkeys(['exopy.LoopTask:exopy.LinspaceLoopInterface',
                                  'LoopTask:__dummy__'])
    errors = {}
    interface_dep_collector.collect(task_workbench, dependencies, errors)
    assert 'exopy.LoopTask:exopy.LinspaceLoopInterface' in dependencies
    assert 'LoopTask:__dummy__' in errors


def test_analysing_instr_task_dependencies(monkeypatch, task_workbench,
                                           task_dep_collector,
                                           profile_dep_collector,
                                           driver_dep_collector):
    """Test analysing the dependencies of a task.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')
    plugin._tasks.contributions['exopy.InstrumentTask'] =\
        TaskInfos(cls=InstrumentTask, instruments=['test'])

    dep = set()
    errors = dict()
    t = InstrumentTask(selected_instrument=('test', 'dummy', 'c', None))
    run = task_dep_collector.analyse(task_workbench, t, getattr,
                                     dep, errors)

    assert run == {'exopy.tasks.instruments.drivers',
                   'exopy.tasks.instruments.profiles'}
    assert 'exopy.InstrumentTask' in dep
    assert not errors

    dep.clear()
    profile_dep_collector.analyse(task_workbench, t, dep, errors)
    assert 'test' in dep
    assert not errors

    dep.clear()
    driver_dep_collector.analyse(task_workbench, t, dep, errors)
    assert 'dummy' in dep
    assert not errors


def test_analysing_instr_interface_dependencies(monkeypatch, task_workbench,
                                                interface_dep_collector,
                                                i_profile_dep_collector,
                                                i_driver_dep_collector):
    """Test analysing the dependencies of an interface.

    """
    class FalseI(TaskInterface):

            __slots__ = ('__dict__')

    plugin = task_workbench.get_plugin('exopy.tasks')
    p_infos = TaskInfos(cls=InstrumentTask, instruments=['test'])
    plugin._tasks.contributions['exopy.InstrumentTask'] = p_infos
    p_infos.interfaces['tasks.FalseI'] =\
        InterfaceInfos(cls=FalseI, instruments=['test'], parent=p_infos)

    dep = set()
    errors = dict()
    i = FalseI()
    t = InstrumentTask(selected_instrument=('test', 'dummy', 'c', None))
    i.task = t
    run = interface_dep_collector.analyse(task_workbench, i, getattr,
                                          dep, errors)

    assert run == {INSTR_RUNTIME_INTERFACE_DRIVERS_ID,
                   INSTR_RUNTIME_INTERFACE_PROFILES_ID}
    assert 'exopy.InstrumentTask:tasks.FalseI' in dep
    assert not errors

    dep.clear()
    i_profile_dep_collector.analyse(task_workbench, i, dep, errors)
    assert 'test' in dep
    assert not errors

    dep.clear()
    i_driver_dep_collector.analyse(task_workbench, i, dep, errors)
    assert 'dummy' in dep
    assert not errors

    i.selected_instrument = ('test2', 'dummy2', 'c', None)

    dep.clear()
    i_profile_dep_collector.analyse(task_workbench, i, dep, errors)
    assert 'test2' in dep
    assert not errors

    dep.clear()
    i_driver_dep_collector.analyse(task_workbench, i, dep, errors)
    assert 'dummy2' in dep
    assert not errors
