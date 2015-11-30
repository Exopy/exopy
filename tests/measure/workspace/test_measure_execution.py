# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test measure execution related widgets.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.testing.measure.fixtures import measure as m_build
from ecpy.testing.util import process_app_events, handle_dialog, CallSpy

with enaml.imports():
    from ecpy.testing.windows import (ContainerTestingWindow,
                                      DockItemTestingWindow)
    from ecpy.measure.workspace.measure_execution import (MeasView,
                                                          ExecutionDockItem)


pytest_plugins = str('ecpy.testing.measure.workspace.fixtures'),


@pytest.fixture
def execution_view(measure_workbench, workspace, windows):
    """Start plugins and add measures before creating the execution view.

    """
    pl = measure_workbench.get_plugin('ecpy.measure')
    pl.enqueued_measures.add(m_build(measure_workbench))
    pl.enqueued_measures.add(m_build(measure_workbench))
    pl.enqueued_measures.measures[1].name = 'dummy_test'
    pl.selected_engine = 'dummy'

    item = ExecutionDockItem(workspace=workspace)
    return DockItemTestingWindow(widget=item)


def test_measure_view(measure, windows, dialog_sleep, monkeypatch, workspace):
    """Test that the displayed buttons do reflect the state of the measure.

    """
    measure.status = 'READY'
    view = MeasView(model=measure)
    w = ContainerTestingWindow(widget=view)

    w.show()
    process_app_events()
    sleep(dialog_sleep)

    assert view.widgets()[2].enabled  # cd1 inserted its children before itself

    def test_state(dial):
        assert dial.measure.status == 'EDITING'

    with handle_dialog('reject', custom=test_state):
        view.widgets()[2].clicked = True

    assert view.widgets()[-1].enabled
    measure.plugin.processor.active = True
    process_app_events()
    assert not view.widgets()[-1].enabled
    process_app_events()
    measure.plugin.processor.active = False

    from ecpy.measure.workspace.workspace import MeasureSpace
    spy = CallSpy()
    monkeypatch.setattr(MeasureSpace, 'process_single_measure', spy)
    view.widgets()[-1].clicked = True
    assert spy.called

    measure.status = 'RUNNING'
    process_app_events()
    assert len(view.widgets()) == 2

    measure.status = 'COMPLETED'
    process_app_events()
    assert len(view.widgets()) == 3
    spy = CallSpy()
    monkeypatch.setattr(MeasureSpace, 'reenqueue_measure', spy)
    view.widgets()[-1].clicked = True

    assert view.widgets()[1].text == 'COMPLETED'


def test_measure_manipulations(execution_view, dialog_sleep):
    """Test moving/removing measure using editor

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    ed = item.dock_widget().widgets()[0]
    meas = item.workspace.plugin.enqueued_measures.measures
    ed.operations['move'](0, 1)
    process_app_events()
    assert meas[0].name == 'dummy_test'

    ed.operations['move'](0, 1)
    process_app_events()
    assert meas[1].name == 'dummy_test'

    ed.operations['remove'](0)
    process_app_events()
    assert meas[0].name == 'dummy_test'
    assert len(meas) == 1


def test_start_button(execution_view, monkeypatch, dialog_sleep):
    """Test that the start button displays the right text and called the
    appropriate method.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    from ecpy.measure.workspace.workspace import MeasureSpace
    spies = {}
    for n in ('start_processing_measures', 'resume_current_measure',
              'pause_current_measure'):
        spy = CallSpy()
        monkeypatch.setattr(MeasureSpace, n, spy)
        spies[n] = spy

    st_btn = item.dock_widget().widgets()[1]
    assert st_btn.enabled
    assert st_btn.text == 'Start'
    st_btn.clicked = True
    process_app_events()
    assert spies['start_processing_measures'].called

    meas = item.workspace.plugin.enqueued_measures.measures[0]
    item.workspace.plugin.processor.running_measure = meas
    item.workspace.plugin.processor.active = True
    process_app_events()
    assert st_btn.enabled
    assert st_btn.text == 'Pause'
    st_btn.clicked = True
    process_app_events()
    assert spies['pause_current_measure'].called

    meas.status = 'PAUSING'
    process_app_events()
    assert not st_btn.enabled

    meas.status = 'PAUSED'
    process_app_events()
    assert st_btn.enabled
    assert st_btn.text == 'Resume'
    st_btn.clicked = True
    process_app_events()
    assert spies['resume_current_measure'].called


def test_stop_button(execution_view, monkeypatch, dialog_sleep):
    """Test the behavoir of the stop button.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    from ecpy.measure.workspace.workspace import MeasureSpace
    spy = CallSpy()
    monkeypatch.setattr(MeasureSpace, 'stop_current_measure', spy)

    with enaml.imports():
        from ecpy.measure.workspace import measure_execution
    qspy = CallSpy()
    monkeypatch.setattr(measure_execution, 'question', qspy)
    st_btn = item.dock_widget().widgets()[2]

    # Check idle state.
    assert not st_btn.enabled
    assert st_btn.text == 'Stop'
    assert not st_btn.stopping

    # Check enabled when running.
    meas = item.workspace.plugin.enqueued_measures.measures[0]
    item.workspace.plugin.processor.running_measure = meas
    item.workspace.plugin.processor.active = True
    assert st_btn.enabled

    # Stop and skip
    item.workspace.plugin.processor.continuous_processing = False
    skip = st_btn.children[0].children[0]
    skip.triggered = True
    process_app_events()
    assert spy.called
    assert spy.kwargs['no_post_exec']
    assert not spy.kwargs['force']
    assert not qspy.called

    # Stop and don't skip
    item.workspace.plugin.processor.continuous_processing = True
    no_skip = st_btn.children[0].children[1]
    no_skip.triggered = True
    process_app_events()
    assert spy.called == 2
    assert not spy.kwargs.get('no_post_exec')
    assert not spy.kwargs['force']
    assert qspy.called
    assert not item.workspace.plugin.processor.continuous_processing

    # Check stopping behavior
    meas.status = 'STOPPING'
    assert st_btn.stopping
    assert st_btn.text == 'Force stop'

    # Check force stopping and no question when no measure remains in queue
    item.workspace.plugin.enqueued_measures.remove(meas)
    qspy.called = 0
    no_skip.triggered = True
    process_app_events()
    assert spy.kwargs['force']
    assert not qspy.called

    spy.kwargs = {}
    skip.triggered = True
    process_app_events()
    assert spy.kwargs['force']
    assert not qspy.called


def test_continuous_processing(execution_view, dialog_sleep):
    """Test that the checkbox does reflect the underlying setting.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget
    ch_box = item.dock_widget().widgets()[3]
    proc = item.workspace.plugin.processor

    assert ch_box.checked == proc.continuous_processing
    ch_box.checked = not proc.continuous_processing
    process_app_events()

    assert ch_box.checked == proc.continuous_processing
    proc.continuous_processing = not ch_box.checked
    process_app_events()

    assert ch_box.checked == proc.continuous_processing


def test_clear(execution_view, dialog_sleep):
    """Test clearing the enqueued measures.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    cl_btn = item.dock_widget().widgets()[4]
    assert cl_btn.enabled

    # Check disabled when running
    meas = item.workspace.plugin.enqueued_measures.measures[0]
    item.workspace.plugin.processor.running_measure = meas
    item.workspace.plugin.processor.active = True
    assert not cl_btn.enabled

    item.workspace.plugin.processor.active = False
    assert cl_btn.enabled

    measures = item.workspace.plugin.enqueued_measures.measures
    measures[0].status = 'COMPLETED'
    measures[1].status = 'FAILED'

    cl_btn.clicked = True
    process_app_events()
    assert not item.workspace.plugin.enqueued_measures.measures
    assert not cl_btn.enabled


def test_show_monitors(execution_view, dialog_sleep):
    """Test restoring the monitor window.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    mon_btn = item.dock_widget().widgets()[5]
    assert not mon_btn.enabled

    with enaml.imports():
        from ecpy.measure.workspace.monitors_window import MonitorsWindow

    meas = item.workspace.plugin.enqueued_measures.measures[0]
    mon_win = MonitorsWindow(item, measure=meas)
    item.workspace.plugin.processor.monitors_window = mon_win

    assert not mon_win.visible

    mon_btn.clicked = True
    process_app_events()
    assert mon_win.visible


def test_engine_status(execution_view, dialog_sleep):
    """Test te display of the engine status.

    """
    execution_view.show()
    process_app_events()
    sleep(dialog_sleep)

    item = execution_view.widget

    en_stat = item.dock_widget().widgets()[-1]
    assert not en_stat.visible

    pl = item.workspace.plugin
    pl.processor.engine = pl.create('engine', 'dummy')
    pl.processor.engine.status = 'Stopped'
    process_app_events()
    assert en_stat.visible

    assert en_stat.widgets()[1].text == 'Stopped'

    meas = item.workspace.plugin.enqueued_measures.measures[0]
    item.workspace.plugin.processor.running_measure = meas
    item.workspace.plugin.processor.active = True

    assert not en_stat.widgets()[2].enabled
    assert en_stat.widgets()[2].text == 'Shut down'
