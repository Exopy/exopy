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
from configobj import ConfigObj

from ecpy.tasks.manager.utils.building import build_task_from_config

from ....util import handle_dialog


#def test_create_task1(task_workbench):
#    """Test creating a task.
#
#    """
#    core = task_workbench.get_plugin('enaml.workbench.core')
#
#    def answer_dialog(dial):
#        pass
#
#    with handle_dialog('accept', answer_dialog):
#        res = core.invoke_command('ecpy.tasks.create')


def test_create_task2(app, task_workbench):
    """Test handling user cancellation.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    with handle_dialog('reject'):
        res = core.invoke_command('ecpy.tasks.create_task')

    assert res is None


@pytest.fixture
def task_config():
    return ConfigObj({'task_class': 'ComplexTask',
                      'dep_type': 'ecpy.task',
                      'name': 'Test'})


def test_build_from_config(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    from ecpy.tasks.api import ComplexTask
    task = build_task_from_config(task_config,
                                  {'ecpy.task': {'ComplexTask': ComplexTask}})

    assert task.name == 'Test'
    assert isinstance(task, ComplexTask)


def test_build_from_config_dependencies_failure(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    task_config['task_class'] = '__dummy__'
    task = build_task_from_config(task_config, task_workbench)

    assert task is None


def test_build_from_config_as_root(task_workbench, task_config):
    """Test creating a root task from a config object.

    """
    task = build_task_from_config(task_config, task_workbench, True)

    assert task.name == 'Root'
    assert type(task).__name__ == 'RootTask'


def test_build_root_from_config(task_workbench):
    """
    """
    pass


def test_build_root_from_template(task_workbench):
    """
    """
    pass
