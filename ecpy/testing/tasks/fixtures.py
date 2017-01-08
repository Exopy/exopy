# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the task manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.tasks.api import RootTask
from ecpy.testing.util import exit_on_err

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest
    from ecpy.app.states.manifest import StateManifest
    from ecpy.app.icons.manifest import IconManagerManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.errors.plugin import ErrorsPlugin
    from ecpy.tasks.manifest import TasksManagerManifest
    from ecpy.tasks.tasks.base_views import RootTaskView

    from ..windows import ContainerTestingWindow

pytests_plugin = str('ecpy.testing.fixtures'),


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

    for m_id in ('ecpy.tasks', 'ecpy.app.dependencies', 'ecpy.app.errors',
                 'ecpy.app.icons', 'ecpy.app.preferences', 'ecpy.app'):
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
