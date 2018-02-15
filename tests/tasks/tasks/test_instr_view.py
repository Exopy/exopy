# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the instrument task view.

"""
import os

import pytest
import enaml
from configobj import ConfigObj

from exopy.testing.util import (handle_dialog,
                                show_and_close_widget)
from exopy.testing.instruments.util import add_profile
from exopy.tasks.api import (RootTask, InstrTaskView, TaskInterface,
                             InstrumentTask, InterfaceableTaskMixin)
from exopy.tasks.infos import TaskInfos, InterfaceInfos
with enaml.imports():
    from exopy.tasks.manifest import TasksManagerManifest
    from exopy.tasks.tasks.base_views import RootTaskView
    from .instrument_contributor import InstrContributor


pytest_plugins = str('exopy.testing.instruments.fixtures'),

PROFILE_PATH = os.path.join(os.path.dirname(__file__), 'fp.instr.ini')


class InterInstrTask(InterfaceableTaskMixin, InstrumentTask):

    task_id = 'exopy.InstrumentTask'


@pytest.fixture
def instr_task_workbench(instr_workbench):
    """Workbench with instrument and task support and patched task.

    """
    w = instr_workbench
    w.register(InstrContributor())
    c = ConfigObj(PROFILE_PATH, encoding='utf-8')
    add_profile(instr_workbench, c, ['fp1', 'fp2', 'fp3', 'fp4'])
    w.register(TasksManagerManifest())
    p = w.get_plugin('exopy.tasks')
    infos = TaskInfos(cls=InterInstrTask,
                      instruments=['tasks.test.FalseDriver'])
    infos.interfaces = \
        {'test.I': InterfaceInfos(cls=TaskInterface, parent=infos,
                                  instruments=['tasks.test.FalseDriver4',
                                               'tasks.test.FalseDriver2']
                                  )
         }
    p._tasks.contributions['exopy.InstrumentTask'] = infos

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


def test_instr_view_display(instr_view, exopy_qtbot):
    """Test displaying the instyr_view.

    """
    show_and_close_widget(exopy_qtbot, instr_view)


def test_profile_filtering(instr_task_workbench, instr_view):
    """Test filtering the profiles allowed for a task.

    """
    c = ConfigObj(PROFILE_PATH, encoding='utf-8')
    c['model_id'] = 'Dummy.dumb.002'
    add_profile(instr_task_workbench, c, ['fp5'])
    p = instr_task_workbench.get_plugin('exopy.instruments')
    filtered = instr_view.filter_profiles(p._profiles)
    assert 'fp5' not in filtered

    c['model_id'] = 'Dummy.dumb.003'
    add_profile(instr_task_workbench, c, ['fp6'])
    p = instr_task_workbench.get_plugin('exopy.instruments')
    filtered = instr_view.filter_profiles(p._profiles)
    assert 'fp6' in filtered


def test_driver_filtering(instr_task_workbench, instr_view):
    """Test filtering the drivers allowed for a task.

    """
    p = instr_task_workbench.get_plugin('exopy.instruments')
    filtered = instr_view.filter_drivers(p._profiles['fp1'].model.drivers)
    assert len(filtered) == 2

    pt = instr_task_workbench.get_plugin('exopy.tasks')
    del pt._tasks.contributions['exopy.InstrumentTask'].interfaces
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


def test_select_instrument(instr_task_workbench, instr_view, exopy_qtbot):
    """Test selecting an instrument from the view.

    """
    tool_btn = instr_view.widgets()[-1].widgets()[-1]
    selec = ('fp1', 'tasks.test.FalseDriver',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    with handle_dialog(exopy_qtbot, 'reject'):
        tool_btn.clicked = True

    assert instr_view.task.selected_instrument == selec

    with handle_dialog(exopy_qtbot, 'accept'):
        tool_btn.clicked = True

    assert instr_view.task.selected_instrument == selec


def test_select_interface_based_on_instrument(instr_task_workbench,
                                              instr_view):
    """Test finding the interface matching the selected instrument.

    """
    instr_view.select_interface()
    assert not instr_view.task.interface

    selec = ('fp1', 'tasks.test.FalseDriver2',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()
    assert instr_view.task.interface

    # Check that moving back to an instrument with no associated interface
    # does discard the interface.
    selec = ('fp1', 'tasks.test.FalseDriver',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()
    assert not instr_view.task.interface

    selec = ('fp1', 'tasks.test.FalseDriver2',
             'false_connection', 'false_settings')
    instr_view.task.selected_instrument = selec
    instr_view.select_interface()

    instr_view.task.selected_instrument = ()
    instr_view.select_interface()
    assert not instr_view.task.interface
