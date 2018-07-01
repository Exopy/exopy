# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test standard task configurers.

"""
import os

import pytest
import enaml

from exopy.testing.util import show_and_close_widget
from exopy.tasks.tasks.base_tasks import RootTask
from exopy.tasks.configs.base_configs import (PyTaskConfig,
                                              TemplateTaskConfig)
with enaml.imports():
    from exopy.tasks.configs.base_config_views\
        import (PyConfigView, TemplateConfigView)


@pytest.mark.ui
def test_py_task_config(exopy_qtbot, task_workbench):
    """Test the basic python task configurer.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')

    root = RootTask()
    config = PyTaskConfig(manager=plugin,
                          task_class=plugin.get_task('exopy.ComplexTask'),
                          future_parent=root)

    assert config.task_name
    assert config.ready
    assert config.task_doc

    config.task_name = ''
    assert not config.ready

    config.task_name = 'Test'
    assert config.ready
    task = config.build_task()
    assert task.name == 'Test'

    root.add_child_task(0, task)
    config2 = PyTaskConfig(manager=plugin,
                           task_class=plugin.get_task('exopy.ComplexTask'),
                           future_parent=root)

    config2.task_name = 'Test'
    assert not config2.ready

    config2.task_name = 'ADifferentName'
    assert config2.ready

    plugin.auto_task_names = []
    config = PyTaskConfig(manager=plugin,
                          task_class=plugin.get_task('exopy.ComplexTask'),
                          future_parent=root)

    assert not config.task_name
    assert not config.ready

    show_and_close_widget(exopy_qtbot, PyConfigView(config=config))
    show_and_close_widget(exopy_qtbot, PyConfigView(config=config, loop=True))


@pytest.mark.ui
def test_template_task_config(exopy_qtbot, task_workbench):
    """Test the template task configurer.

    """
    plugin = task_workbench.get_plugin('exopy.tasks')

    path = os.path.join(os.path.dirname(__file__),
                        'test_template.task.ini')
    root = RootTask()
    config = TemplateTaskConfig(manager=plugin,
                                template_path=path,
                                future_parent=root)
    assert config.template_doc
    task = config.build_task()
    assert len(task.children) == 1

    show_and_close_widget(exopy_qtbot, TemplateConfigView(config=config))
