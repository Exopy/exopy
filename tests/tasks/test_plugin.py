# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the functionality of the tasks manager..

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
from time import sleep

import pytest
import enaml

from ecpy.tasks.infos import TaskInfos, InterfaceInfos


def test_lifecycle(task_workbench):
    """Test the task manager life cycle.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    assert 'ecpy.ComplexTask' in plugin._tasks.contributions
    assert 'All' in plugin._filters.contributions
    from ecpy.tasks.tasks.base_tasks import BaseTask
    assert BaseTask in plugin._configs.contributions
    assert 'All' in plugin.filters

    assert plugin.auto_task_names

    plugin.stop()


def test_observer_error(task_workbench, monkeypatch):
    """Test handling an error when trying to join the observer.

    """
    from ecpy.tasks.plugin import Observer

    def false_join(self):
        raise RuntimeError
    monkeypatch.setattr(Observer, 'join', false_join)

    plugin = task_workbench.get_plugin('ecpy.tasks')

    plugin.stop()


def test_template_observation(task_workbench, app_dir, monkeypatch):
    """Test template folders observations and handling of new template folders.

    Force using PollingObserver to make this run on Travis CI.

    """
    from watchdog.observers.polling import PollingObserver
    from ecpy.tasks import plugin
    monkeypatch.setattr(plugin, 'Observer', PollingObserver)

    plugin = task_workbench.get_plugin('ecpy.tasks')

    template = os.path.join(app_dir, 'tasks', 'templates', 'test.task.ini')
    with open(template, 'wb'):
        pass

    assert os.path.isfile(template)

    sleep(1.2)

    assert 'test' in plugin.templates


def test_handle_wrong_template_dir(task_workbench, caplog):
    """Test that an incorrect path in _profiles_dirs does not crash anything.

    """
    p = task_workbench.get_plugin('ecpy.tasks')

    p._template_folders = ['dummy']
    p._refresh_templates()

    for records in caplog.records():
        assert records.levelname == 'WARNING'


def test_list_tasks(task_workbench):
    """Test listing the known tasks using different filters.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    tasks = task_workbench.get_plugin('ecpy.tasks')
    tasks.templates['test'] = ''

    cmd = 'ecpy.tasks.list_tasks'
    t = core.invoke_command(cmd)
    assert 'test' in t
    assert 'ecpy.ComplexTask' in t

    t = core.invoke_command(cmd, dict(filter='Logic'))
    assert 'test' not in t
    assert 'ecpy.ComplexTask' not in t

    t = core.invoke_command(cmd, dict(filter='Templates'))
    assert 'test' in t
    assert 'ecpy.ComplexTask' not in t

    t = core.invoke_command(cmd, dict(filter='Python'))
    assert 'test' not in t
    assert 'ecpy.ComplexTask' in t


def test_available_filters_update(task_workbench):
    """Check that the list of available filters is update when the
    contributions are.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    filters = {'rr': 'r'}
    plugin._filters.contributions = filters

    assert plugin.filters == list(filters)


def test_get_task_infos(task_workbench):
    """Test getting a task infos.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_task_infos'
    t = core.invoke_command(cmd, dict(task='ecpy.ComplexTask'))
    assert isinstance(t, TaskInfos)
    from ecpy.tasks.api import ComplexTask
    assert t.cls is ComplexTask

    assert core.invoke_command(cmd, dict(task='')) is None


def test_get_task(task_workbench):
    """Test accessing a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_task'
    t = core.invoke_command(cmd, dict(task='ecpy.ComplexTask', view=True))
    from ecpy.tasks.api import ComplexTask
    assert t[0] is ComplexTask
    with enaml.imports():
        from ecpy.tasks.tasks.base_views import ComplexTaskView
    assert t[1] is ComplexTaskView

    assert core.invoke_command(cmd, dict(task='')) is None


def test_get_tasks(task_workbench):
    """Test accessing multiple tasks.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_tasks'
    t = core.invoke_command(cmd, dict(tasks=['ecpy.LoopTask',
                                             'ecpy.ComplexTask', '']))
    assert len(t[0]) == 2
    assert t[1] == ['']


LINSPACE_INTERFACE = 'ecpy.LoopTask:ecpy.LinspaceLoopInterface'


def test_get_interface_infos(task_workbench):
    """Test accessing an interface infos.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_interface_infos'
    t = core.invoke_command(cmd, dict(interface=LINSPACE_INTERFACE))
    assert isinstance(t, InterfaceInfos)
    from ecpy.tasks.tasks.logic.loop_linspace_interface\
        import LinspaceLoopInterface
    assert t.cls is LinspaceLoopInterface

    assert core.invoke_command(cmd, dict(interface=':')) is None
    assert (core.invoke_command(cmd, dict(interface='ecpy.LoopTask:'))
            is None)


def test_get_interface(task_workbench):
    """Test accessing a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_interface'
    t = core.invoke_command(cmd,
                            dict(interface=LINSPACE_INTERFACE, views=True))
    from ecpy.tasks.tasks.logic.loop_linspace_interface\
        import LinspaceLoopInterface
    assert t[0] is LinspaceLoopInterface
    assert len(t[1]) == 1

    assert core.invoke_command(cmd, dict(interface=':')) is None


def test_get_interfaces(task_workbench):
    """Test accessing multiple tasks.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_interfaces'
    t = core.invoke_command(cmd, dict(interfaces=[LINSPACE_INTERFACE,
                                                  ':']))
    assert len(t[0]) == 1
    assert t[1] == [':']


def test_get_config_from_name(task_workbench):
    """Test getting a config for a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_config'
    c = core.invoke_command(cmd, dict(task_id='ecpy.LoopTask'))
    assert type(c[0]).__name__ == 'LoopTaskConfig'


def test_get_config_for_template(task_workbench):
    """Test getting a config for a template.

    """
    tasks = task_workbench.get_plugin('ecpy.tasks')
    tasks.templates['test'] = ''

    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_config'
    c = core.invoke_command(cmd, dict(task_id='test'))
    assert type(c[0]).__name__ == 'TemplateTaskConfig'


def test_get_config_for_unknown(task_workbench):
    """Test getting a config for an unknown task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    cmd = 'ecpy.tasks.get_config'
    c = core.invoke_command(cmd, dict(task_id=''))
    assert c == (None, None)


def test_load_auto_task_names1(task_workbench):
    """Test loading of  default task names.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')
    assert plugin.auto_task_names


def test_load_auto_task_names2(task_workbench, windows):
    """Test automatic loading of default task names: wrong path.

    """
    plugin = task_workbench.get_plugin('ecpy.app.preferences')
    plugin._prefs['ecpy.tasks'] = {}
    plugin._prefs['ecpy.tasks']['auto_task_path'] = '__'

    with pytest.raises(Exception):
        task_workbench.get_plugin('ecpy.tasks')
