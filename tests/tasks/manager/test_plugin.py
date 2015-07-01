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

import pytest


def test_lifecycle(task_workbench):
    """Test the task manager life cycle.

    """
    plugin = task_workbench.get_plugin('ecpy.tasks')

    assert 'ComplexTask' in plugin._tasks.contributions
    assert 'All' in plugin._filters.contributions
    assert 'BaseTask' in plugin._configs.contributions

    assert plugin.auto_task_names

    plugin.stop()


def test_template_folder_creation_issue(task_workbench, monkeypatch):
    """Test handling an error when attempting to create the template dir.

    """
    from ecpy.tasks.manager import plugin
    monkeypatch.setattr(plugin, 'TEMPLATE_PATH', '*')

    monkeypatch.setattr(plugin.TaskManagerPlugin, 'templates_folders', ['*'])

    with pytest.raises(Exception):
        task_workbench.get_plugin('ecpy.tasks')


def test_list_tasks():
    """
    """
    pass


def test_get_task_infos():
    """
    """
    pass


def test_get_task():
    """
    """
    pass


def test_get_tasks():
    """
    """
    pass


def test_get_interface_infos():
    """
    """
    pass


def test_get_interface():
    """
    """
    pass


def test_get_interfaces():
    """
    """
    pass


def test_get_config():
    """
    """
    pass


def test_load_auto_task_names():
    """
    """
    pass
