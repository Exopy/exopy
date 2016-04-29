# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test dependency collection functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from operator import getitem

import pytest
from future.builtins import str

from ecpy.app.dependencies.api import (BuildDependency,
                                       RuntimeDependencyAnalyser)
from ecpy.tasks.api import ComplexTask, InstrumentTask
from ecpy.tasks.infos import TaskInfos


@pytest.fixture
def task_dep_collector(task_workbench):
    """Collector for task dependencies.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'build_deps'][0]
    return [b for b in dep_ext.get_children(BuildDependency)
            if b.id == 'ecpy.task'][0]


@pytest.fixture
def interface_dep_collector(task_workbench):
    """Collector for interface dependencies.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'build_deps'][0]
    return [b for b in dep_ext.get_children(BuildDependency)
            if b.id == 'ecpy.tasks.interface'][0]


@pytest.fixture
def driver_dep_collector(task_workbench):
    """Collector for driver dependencies (InstrumentTask).

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == 'ecpy.tasks.instruments.drivers'][0]


@pytest.fixture
def profile_dep_collector(task_workbench):
    """Collector for profile dependencies (InstrumentTask).

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    dep_ext = [e for e in plugin.manifest.extensions
               if e.id == 'runtime_deps'][0]
    return [b for b in dep_ext.get_children(RuntimeDependencyAnalyser)
            if b.id == 'ecpy.tasks.instruments.profiles'][0]


def test_analysing_task_dependencies(monkeypatch, task_workbench,
                                     task_dep_collector):
    """Test analysing the dependencies of a task.

    """
    runtime = {'test'}
    plugin = task_workbench.get_plugin('ecpy.tasks')
    monkeypatch.setattr(plugin.get_task_infos('ecpy.ComplexTask'),
                        'dependencies', runtime)

    dep = set()
    errors = dict()
    run = task_dep_collector.analyse(task_workbench, ComplexTask(), getattr,
                                     dep, errors)

    assert run == runtime
    assert 'ecpy.ComplexTask' in dep
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
                                {'ecpy.ComplexTask', '__dummy__'}, errors)
    assert 'ecpy.ComplexTask' not in errors
    assert '__dummy__' in errors


def test_collecting_task_dependencies(task_workbench, task_dep_collector):
    """Test collecting the dependencies found in a task.

    """
    dependencies = dict.fromkeys(['ecpy.ComplexTask', '__dummy__'])
    errors = {}
    task_dep_collector.collect(task_workbench, dependencies, errors)
    assert 'ecpy.ComplexTask' in dependencies
    assert '__dummy__' in errors


def test_analysing_interface_dependencies(monkeypatch, task_workbench,
                                          interface_dep_collector):
    """Test analysing the dependencies in an interface.

    """
    runtime = {'test'}
    interface = ('LinspaceLoopInterface', 'ecpy.LoopTask')
    plugin = task_workbench.get_plugin('ecpy.tasks')
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
                                              ('__dummy__', 'LoopTask')},
                                          getitem, dep, errors)
    assert not run
    assert not dep
    assert str(('__dummy__', 'LoopTask')) in errors


def test_validating_interface_dependencies(task_workbench,
                                           interface_dep_collector):
    """Test validating interface dependencies.

    """
    errors = {}
    interface_dep_collector.validate(task_workbench,
                                     {('LinspaceLoopInterface',
                                       'ecpy.LoopTask'),
                                      ('__dummy__', 'LoopTask')}, errors)
    assert ('LinspaceLoopInterface', 'ecpy.LoopTask') not in errors
    assert ('__dummy__', 'LoopTask') in errors


def test_collecting_interface_dependencies(task_workbench,
                                           interface_dep_collector):
    """Test collecting the dependencies found in an interface.

    """
    dependencies = dict.fromkeys([('LinspaceLoopInterface', 'ecpy.LoopTask'),
                                  ('__dummy__', 'LoopTask')])
    errors = {}
    interface_dep_collector.collect(task_workbench, dependencies, errors)
    assert ('LinspaceLoopInterface', 'ecpy.LoopTask') in dependencies
    assert ('__dummy__', 'LoopTask') in errors


def test_analysing_instr_task_dependencies(monkeypatch, task_workbench,
                                           task_dep_collector,
                                           profile_dep_collector,
                                           driver_dep_collector):
    """Test analysing the dependencies of a task.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    plugin._tasks.contributions['ecpy.InstrumentTask'] =\
        TaskInfos(cls=InstrumentTask, instruments=['test'])

    dep = set()
    errors = dict()
    t = InstrumentTask(selected_instrument=('test', 'dummy', 'c', None))
    run = task_dep_collector.analyse(task_workbench, t, getattr,
                                     dep, errors)

    assert run == {'ecpy.tasks.instruments.drivers',
                   'ecpy.tasks.instruments.profiles'}
    assert 'ecpy.InstrumentTask' in dep
    assert not errors

    dep.clear()
    profile_dep_collector.analyse(task_workbench, t, dep, errors)
    assert 'test' in dep
    assert not errors

    dep.clear()
    driver_dep_collector.analyse(task_workbench, t, dep, errors)
    assert 'dummy' in dep
    assert not errors
