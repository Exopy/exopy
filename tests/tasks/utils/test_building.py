# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test task building utility functions.

"""
import pytest
from configobj import ConfigObj

from exopy.tasks.utils.building import build_task_from_config

from exopy.testing.util import handle_dialog


def test_create_task1(exopy_qtbot, task_workbench):
    """Test creating a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    def answer_dialog(bot, dial):
        selector = dial.selector
        selector.selected_filter = 'Logic'
        selector.selected_task = 'exopy.WhileTask'
        dial.config.task_name = 'Test'

        def assert_dial_config_ready():
            assert dial.config.ready
        bot.wait_until(assert_dial_config_ready)

    with handle_dialog(exopy_qtbot, 'accept', answer_dialog):
        res = core.invoke_command('exopy.tasks.create_task')
        assert res


def test_create_task2(exopy_qtbot, task_workbench, dialog_sleep):
    """Test handling user cancellation.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    def answer_dialog(exopy_qtbot, dial):
        selector = dial.selector
        qlist = selector.widgets()[-1]
        qlist.selected_item = qlist.items[-1]

        def assert_dial_config():
            assert dial.config
        exopy_qtbot.wait_until(assert_dial_config)
        exopy_qtbot.wait(dialog_sleep)

        dial._choose_config('_dummy_')
        assert not dial.config
        exopy_qtbot.wait(dialog_sleep)

    with handle_dialog(exopy_qtbot, 'reject', answer_dialog):
        res = core.invoke_command('exopy.tasks.create_task')

    assert res is None


@pytest.fixture
def task_config():
    return ConfigObj({'task_id': 'exopy.ComplexTask',
                      'dep_type': 'exopy.task',
                      'name': 'Test'})


def test_build_from_config(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    from exopy.tasks.api import ComplexTask
    task = build_task_from_config(task_config,
                                  {'exopy.task':
                                      {'exopy.ComplexTask': ComplexTask}})

    assert task.name == 'Test'
    assert isinstance(task, ComplexTask)


def test_build_from_config_analyse_dep_failure(task_workbench, task_config):
    """Test creating a task from a config object.

    """
    task_config['task_id'] = '__dummy__'
    with pytest.raises(RuntimeError):
        build_task_from_config(task_config, task_workbench)


def test_build_from_config_collecting_dep_failure(task_workbench, task_config,
                                                  monkeypatch):
    """Test creating a task from a config object.

    """
    plugin = task_workbench.get_plugin('exopy.app.dependencies')
    cls = type(plugin.build_deps.contributions['exopy.task'])

    class FalseCollector(cls):
        def collect(self, kind, dependencies, owner=None):
            raise RuntimeError()

    monkeypatch.setitem(plugin.build_deps.contributions, 'exopy.task',
                        FalseCollector())
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

    task = core.invoke_command('exopy.tasks.build_root',
                               dict(mode='from config', config=task_config,
                                    build_dep={}))
    assert task.name == 'Root'


def test_build_root_from_template(exopy_qtbot, tmpdir, task_workbench,
                                  task_config):
    """Test creating a root task from a template.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    plugin = task_workbench.get_plugin('exopy.tasks')
    path = str(tmpdir.join('temp.task.ini'))
    task_config.filename = path
    task_config.write()
    plugin.templates['temp.task.ini'] = path

    def answer_dialog(bot, dial):
        selector = dial.selector
        selector.selected_task = 'temp.task.ini'
        assert dial.path == path

    with handle_dialog(exopy_qtbot, 'accept', answer_dialog):
        task = core.invoke_command('exopy.tasks.build_root',
                                   dict(mode='from template'))
    assert task.name == 'Root'
