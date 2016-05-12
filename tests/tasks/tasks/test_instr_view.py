# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the instrument task view.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
import enaml
from configobj import ConfigObj

from ecpy.testing.util import (handle_dialog,
                               show_and_close_widget)
from ecpy.tasks.api import (RootTask, InstrTaskView, TaskInterface,
                            InstrumentTask, InterfaceableTaskMixin)
from ecpy.tasks.infos import TaskInfos, InterfaceInfos
with enaml.imports():
    from ecpy.tasks.manifest import TasksManagerManifest
    from ecpy.tasks.tasks.base_views import RootTaskView

from ...instruments.conftest import PROFILE_PATH, prof_plugin

pytest_plugins = str('ecpy.testing.instruments.fixtures'),


class InterInstrTask(InterfaceableTaskMixin, InstrumentTask):

    task_id = 'ecpy.InstrumentTask'


def add_profile(workbench, name, model):
    """Add a new instrument profiles for a given model.

    """
    p_plugin = workbench.get_plugin('ecpy.instruments')
    c = ConfigObj(PROFILE_PATH, encoding='utf-8')
    c['model_id'] = model
    with open(os.path.join(p_plugin._profiles_folders[0], name + '.instr.ini'),
              'wb') as f:
        c.write(f)

    p_plugin._refresh_profiles()


@pytest.fixture
def instr_task_workbench(prof_plugin):
    """Workbench with instrument and task support and patched task.

    """
    w = prof_plugin.workbench
    w.register(TasksManagerManifest())
    p = w.get_plugin('ecpy.tasks')
    infos = TaskInfos(cls=InterInstrTask,
                      instruments=['tests.test.FalseDriver'])
    infos.interfaces = {'test.I':
                        InterfaceInfos(cls=TaskInterface, parent=infos,
                                       instruments=['tests.test.FalseDriver4',
                                                    'tests.test.FalseDriver2'],
                                       )
                        }
    p._tasks.contributions['ecpy.InstrumentTask'] = infos

    return w


@pytest.fixture
def instr_view(instr_task_workbench):
    """Initialize a instr view.

    """
    c = instr_task_workbench.get_plugin('enaml.workbench.core')
    task = RootTask()
    view = RootTaskView(task=task, core=c)
    i_view = InstrTaskView(task=InterInstrTask(root=task), root=view)
    i_view.set_parent(view)
    return i_view


def test_instr_view_display(instr_view):
    """Test displaying the instyr_view.

    """
    show_and_close_widget(instr_view)


def test_profile_filtering(instr_task_workbench, instr_view):
    """Test filtering the profiles allowed for a task.

    """
    add_profile(instr_task_workbench, 'fp5', 'Dummy.dumb.002')
    p = instr_task_workbench.get_plugin('ecpy.instruments')
    filtered = instr_view.filter_profiles(p._profiles)
    assert 'fp5' not in filtered

    add_profile(instr_task_workbench, 'fp6', 'Dummy.dumb.003')
    p = instr_task_workbench.get_plugin('ecpy.instruments')
    filtered = instr_view.filter_profiles(p._profiles)
    assert 'fp6' in filtered


def test_driver_filtering(instr_task_workbench, instr_view):
    """Test filtering the drivers allowed for a task.

    """
    p = instr_task_workbench.get_plugin('ecpy.instruments')
    filtered = instr_view.filter_drivers(p._profiles['fp1'].model.drivers)
    assert len(filtered) == 2

    pt = instr_task_workbench.get_plugin('ecpy.tasks')
    del pt._tasks.contributions['ecpy.InstrumentTask'].interfaces
    filtered = instr_view.filter_drivers(p._profiles['fp1'].model.drivers)
    assert len(filtered) == 1


def test_make_tooltip(instr_view):
    """Test building the tool tip based on the selected instrument.

    """
    selected = ('p', 'd', 'c', None)
    t = instr_view.make_selected_instrument_tooltip(selected)
    assert 'settings' not in t

    selected = ('p', 'd', 'c', 's')
    t = instr_view.make_selected_instrument_tooltip(selected)
    assert 'settings' in t


def test_select_instrument(instr_task_workbench, instr_view):
    """Test selecting an instrument from the view.

    """
    tool_btn = instr_view.widgets()[-1].widgets()[-1]
    selec = ('fp1', 'tests.test.FalseDriver',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    with handle_dialog('reject'):
        tool_btn.clicked = True

    assert instr_view.task.selected_instrument == selec

    with handle_dialog('accept'):
        tool_btn.clicked = True

    assert instr_view.task.selected_instrument == selec


def test_select_interface_based_on_instrument(instr_task_workbench,
                                              instr_view):
    """Test finding the interface matching the selected instrument.

    """
    instr_view.select_interface()
    assert not instr_view.task.interface

    selec = ('fp1', 'tests.test.FalseDriver2',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()
    assert instr_view.task.interface

    # Check that moving back to an instrument with no associated interface
    # does discard the interface.
    selec = ('fp1', 'tests.test.FalseDriver',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()
    assert not instr_view.task.interface

    selec = ('fp1', 'tests.test.FalseDriver2',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()

    instr_view.task.selected_instrument = ()
    instr_view.select_interface()
    assert not instr_view.task.interface
