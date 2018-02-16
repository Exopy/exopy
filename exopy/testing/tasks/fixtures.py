# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the task manager plugin.

"""
from time import sleep

import pytest
import enaml

from exopy.tasks.api import RootTask
from exopy.testing.util import exit_on_err

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from exopy.app.app_manifest import AppManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.dependencies.manifest import DependenciesManifest
    from exopy.app.states.manifest import StateManifest
    from exopy.app.icons.manifest import IconManagerManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.errors.plugin import ErrorsPlugin
    from exopy.tasks.manifest import TasksManagerManifest
    from exopy.tasks.tasks.base_views import RootTaskView

    from ..windows import ContainerTestingWindow

pytests_plugin = str('exopy.testing.fixtures'),


@pytest.yield_fixture
def task_workbench(workbench, monkeypatch, app_dir):
    """Setup the workbench in such a way that the task manager can be tested.

    """
    monkeypatch.setattr(ErrorsPlugin, 'exit_error_gathering', exit_on_err)

    workbench.register(CoreManifest())
    workbench.register(AppManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())
    workbench.register(ErrorsManifest())
    workbench.register(StateManifest())
    workbench.register(DependenciesManifest())
    workbench.register(TasksManagerManifest())

    yield workbench

    for m_id in ('exopy.tasks', 'exopy.app.dependencies', 'exopy.app.errors',
                 'exopy.app.icons', 'exopy.app.preferences', 'exopy.app'):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass

        # Give some time to the os to release resources linked to file
        # monitoring.
        sleep(0.1)


@pytest.fixture
def root_view(task_workbench):
    """Initialize a root view.

    """
    c = task_workbench.get_plugin('enaml.workbench.core')
    task = RootTask()
    view = RootTaskView(task=task, core=c)
    w = ContainerTestingWindow(workbench=task_workbench)
    view.set_parent(w)
    return view
