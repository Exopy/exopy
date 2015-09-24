# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test task building utility functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from future.builtins import str
from configobj import ConfigObj

from ecpy.tasks.manager.utils.building import build_task_from_config

from ....util import handle_dialog, process_app_events


def test_create_task1(app, task_workbench):
    """Test creating a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    def answer_dialog(dial):
        selector = dial.selector
        selector.selected_filter = 'Logic'
        selector.selected_task = 'WhileTask'
        dial.config.task_name = 'Test'
        process_app_events()
        assert dial.config.ready

    with handle_dialog('accept', answer_dialog):
        res = core.invoke_command('ecpy.tasks.create_task')
        assert res


def test_create_task2(app, task_workbench):
    """Test handling user cancellation.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    with handle_dialog('reject'):
        res = core.invoke_command('ecpy.tasks.create_task')

    assert res is None


@pytest.fixture
def task_config():
    return ConfigObj({'task_id': 'ecpy.ComplexTask',
                      'dep_type': 'ecpy.task',
                      'name': 'Test'})


def test_build_from_config(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    from ecpy.tasks.api import ComplexTask
    task = build_task_from_config(task_config,
                                  {'ecpy.task':
                                      {'ecpy.ComplexTask': ComplexTask}})

    assert task.name == 'Test'
    assert isinstance(task, ComplexTask)


def test_build_from_config_dependencies_failure(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    task_config['task_id'] = '__dummy__'
    with pytest.raises(RuntimeError):
        build_task_from_config(task_config, task_workbench)


def test_build_from_config_as_root(task_workbench, task_config):
    """Test creating a root task from a config object.

    """
    task = build_task_from_config(task_config, task_workbench, True)

    assert task.name == 'Root'
    assert type(task).__name__ == 'RootTask'


def test_build_root_from_config(task_workbench, task_config):
    """Test creating a root task from a config dictionary.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    task = core.invoke_command('ecpy.tasks.build_root',
                               dict(mode='from config', config=task_config,
                                    build_dep={}))
    assert task.name == 'Root'


def test_build_root_from_template(tmpdir, task_workbench, task_config):
    """Test creating a root task from a template.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    plugin = task_workbench.get_plugin('ecpy.tasks')
    path = str(tmpdir.join('temp.task.ini'))
    task_config.filename = path
    task_config.write()
    plugin.templates['temp.task.ini'] = path

    def answer_dialog(dial):
        selector = dial.selector
        selector.selected_task = 'temp.task.ini'
        assert dial.path == path

    with handle_dialog('accept', answer_dialog):
        task = core.invoke_command('ecpy.tasks.build_root',
                                   dict(mode='from template'))
    assert task.name == 'Root'
