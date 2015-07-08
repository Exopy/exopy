# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test standard task configurers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
import enaml

from ecpy.tasks.manager.configs.base_configs import (PyTaskConfig,
                                                     TemplateTaskConfig)
with enaml.imports():
    from ecpy.tasks.manager.configs.base_config_views\
        import (PyConfigView, TemplateConfigView)

from ....util import show_and_close_widget


@pytest.mark.ui
def test_py_task_config(app, task_workbench):
    """Test the basic python task configurer.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    config = PyTaskConfig(manager=plugin,
                          task_class=plugin.get_task('ComplexTask'))

    assert config.task_name
    assert config.ready
    assert config.task_doc

    config.task_name = ''
    assert not config.ready

    config.task_name = 'Test'
    task = config.build_task()
    assert task.name == 'Test'

    plugin.auto_task_names = []
    config = PyTaskConfig(manager=plugin,
                          task_class=plugin.get_task('ComplexTask'))

    assert not config.task_name
    assert not config.ready

    show_and_close_widget(PyConfigView(config=config))
    show_and_close_widget(PyConfigView(config=config, loop=True))


@pytest.mark.ui
def test_template_task_config(app, task_workbench):
    """Test the template task configurer.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    path = os.path.join(os.path.dirname(__file__),
                        'test_template.template.ini')
    config = TemplateTaskConfig(manager=plugin,
                                template_path=path)
    assert config.template_doc
    task = config.build_task()
    assert len(task.children) == 1

    show_and_close_widget(TemplateConfigView(config=config))
