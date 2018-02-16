# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test measurement execution related widgets.

"""
import pytest
import enaml

from exopy.testing.measurement.fixtures import measurement as m_build
from exopy.testing.util import (handle_dialog, wait_for_window_displayed,
                                CallSpy)

with enaml.imports():
    from exopy.testing.windows import (ContainerTestingWindow,
                                       DockItemTestingWindow)
    from exopy.measurement.workspace.measurement_execution\
        import MeasView, ExecutionDockItem


pytest_plugins = str('exopy.testing.measurement.workspace.fixtures'),


@pytest.fixture
def execution_view(measurement_workbench, workspace, exopy_qtbot):
    """Start plugins and add measurements before creating the execution view.

    """
    pl = measurement_workbench.get_plugin('exopy.measurement')
    pl.enqueued_measurements.add(m_build(measurement_workbench))
    pl.enqueued_measurements.add(m_build(measurement_workbench))
    pl.enqueued_measurements.measurements[1].name = 'dummy_test'
    pl.selected_engine = 'dummy'
    engine = pl.create('engine', pl.selected_engine)
    pl.processor.engine = engine

    item = ExecutionDockItem(workspace=workspace)
    return DockItemTestingWindow(widget=item)


def test_measurement_view(measurement, exopy_qtbot, dialog_sleep, monkeypatch,
                          workspace):
    """Test that the displayed buttons do reflect the state of the measurement.

    """
    measurement.status = 'READY'
    view = MeasView(model=measurement)
    w = ContainerTestingWindow(widget=view)

    w.show()
    wait_for_window_displayed(exopy_qtbot, w)
    exopy_qtbot.wait(dialog_sleep)

    assert view.widgets()[2].enabled  # cd1 inserted its children before itself

    def test_state(bot, dial):
        assert dial.measurement.status == 'EDITING'

    with handle_dialog(exopy_qtbot, 'reject', handler=test_state):
        view.widgets()[2].clicked = True

    assert view.widgets()[-1].enabled
    measurement.plugin.processor.active = True

    def assert_enabled():
        assert not view.widgets()[-1].enabled
    exopy_qtbot.wait_until(assert_enabled)
    measurement.plugin.processor.active = False

    from exopy.measurement.workspace.workspace import MeasurementSpace
    spy = CallSpy()
    monkeypatch.setattr(MeasurementSpace, 'process_single_measurement', spy)
    view.widgets()[-1].clicked = True
    assert spy.called

    measurement.status = 'RUNNING'

    def assert_widgets():
        assert len(view.widgets()) == 2
    exopy_qtbot.wait_until(assert_widgets)

    measurement.status = 'COMPLETED'

    def assert_widgets():
        assert len(view.widgets()) == 3
    exopy_qtbot.wait_until(assert_widgets)
    spy = CallSpy()
    monkeypatch.setattr(MeasurementSpace, 'reenqueue_measurement', spy)
    view.widgets()[-1].clicked = True

    assert view.widgets()[1].text == 'COMPLETED'


def test_measurement_manipulations(exopy_qtbot, execution_view, dialog_sleep):
    """Test moving/removing measurement using editor

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget

    ed = item.dock_widget().widgets()[0]
    meas = item.workspace.plugin.enqueued_measurements.measurements
    ed.operations['move'](0, 1)

    def assert_meas_name():
        assert meas[0].name == 'dummy_test'
    exopy_qtbot.wait_until(assert_meas_name)

    ed.operations['move'](0, 1)

    def assert_meas_name():
        assert meas[1].name == 'dummy_test'
    exopy_qtbot.wait_until(assert_meas_name)

    ed.operations['remove'](0)

    def assert_meas_name():
        assert meas[0].name == 'dummy_test'
    exopy_qtbot.wait_until(assert_meas_name)
    assert len(meas) == 1


def test_start_button(exopy_qtbot, execution_view, monkeypatch, dialog_sleep):
    """Test that the start button displays the right text and called the
    appropriate method.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget

    from exopy.measurement.workspace.workspace import MeasurementSpace
    spies = {}
    for n in ('start_processing_measurements', 'resume_current_measurement',
              'pause_current_measurement'):
        spy = CallSpy()
        monkeypatch.setattr(MeasurementSpace, n, spy)
        spies[n] = spy

    st_btn = item.dock_widget().widgets()[1]
    assert st_btn.enabled
    assert st_btn.text == 'Start'
    st_btn.clicked = True

    def assert_called():
        assert spies['start_processing_measurements'].called
    exopy_qtbot.wait_until(assert_called)

    meas = item.workspace.plugin.enqueued_measurements.measurements[0]
    item.workspace.plugin.processor.running_measurement = meas
    item.workspace.plugin.processor.active = True

    def assert_enabled():
        assert st_btn.enabled
        assert st_btn.text == 'Pause'
    exopy_qtbot.wait_until(assert_enabled)

    st_btn.clicked = True

    def assert_called():
        assert spies['pause_current_measurement'].called
    exopy_qtbot.wait_until(assert_called)

    meas.status = 'PAUSING'

    def assert_enabled():
        assert not st_btn.enabled
    exopy_qtbot.wait_until(assert_enabled)

    meas.status = 'PAUSED'

    def assert_enabled():
        assert st_btn.enabled
    assert st_btn.text == 'Resume'
    exopy_qtbot.wait_until(assert_enabled)

    st_btn.clicked = True

    def assert_called():
        assert spies['resume_current_measurement'].called
    exopy_qtbot.wait_until(assert_called)


def test_stop_button(exopy_qtbot, execution_view, monkeypatch, dialog_sleep):
    """Test the behavoir of the stop button.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget

    from exopy.measurement.workspace.workspace import MeasurementSpace
    spy = CallSpy()
    monkeypatch.setattr(MeasurementSpace, 'stop_current_measurement', spy)

    with enaml.imports():
        from exopy.measurement.workspace import measurement_execution
    qspy = CallSpy()
    monkeypatch.setattr(measurement_execution, 'question', qspy)
    st_btn = item.dock_widget().widgets()[2]

    # Check idle state.
    assert not st_btn.enabled
    assert st_btn.text == 'Stop'
    assert not st_btn.stopping

    # Check enabled when running.
    meas = item.workspace.plugin.enqueued_measurements.measurements[0]
    item.workspace.plugin.processor.running_measurement = meas
    item.workspace.plugin.processor.active = True
    assert st_btn.enabled

    # Stop and skip
    item.workspace.plugin.processor.continuous_processing = False
    skip = st_btn.children[0].children[0]
    skip.triggered = True

    def assert_called():
        assert spy.called
        assert spy.kwargs['no_post_exec']
        assert not spy.kwargs['force']
        assert not qspy.called
    exopy_qtbot.wait_until(assert_called)

    # Stop and don't skip
    item.workspace.plugin.processor.continuous_processing = True
    no_skip = st_btn.children[0].children[1]
    no_skip.triggered = True

    def assert_called():
        assert spy.called == 2
        assert not spy.kwargs.get('no_post_exec')
        assert not spy.kwargs['force']
        assert qspy.called
        assert not item.workspace.plugin.processor.continuous_processing
    exopy_qtbot.wait_until(assert_called)

    # Check stopping behavior
    meas.status = 'STOPPING'
    assert st_btn.stopping
    assert st_btn.text == 'Force stop'

    # Check force stopping and no question when no measurement remains in queue
    item.workspace.plugin.enqueued_measurements.remove(meas)
    qspy.called = 0
    no_skip.triggered = True

    def assert_called():
        assert spy.kwargs['force']
        assert not qspy.called
    exopy_qtbot.wait_until(assert_called)

    spy.kwargs = {}
    skip.triggered = True

    def assert_called():
        assert spy.kwargs['force']
        assert not qspy.called
    exopy_qtbot.wait_until(assert_called)


def test_continuous_processing(exopy_qtbot, execution_view, dialog_sleep):
    """Test that the checkbox does reflect the underlying setting.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget
    ch_box = item.dock_widget().widgets()[3]
    proc = item.workspace.plugin.processor

    def assert_checked():
        assert ch_box.checked == proc.continuous_processing

    assert_checked()
    ch_box.checked = not proc.continuous_processing

    exopy_qtbot.wait_until(assert_checked)

    proc.continuous_processing = not ch_box.checked

    exopy_qtbot.wait_until(assert_checked)


def test_clear(exopy_qtbot, execution_view, dialog_sleep):
    """Test clearing the enqueued measurements.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget

    cl_btn = item.dock_widget().widgets()[4]
    assert cl_btn.enabled

    # Check disabled when running
    meas = item.workspace.plugin.enqueued_measurements.measurements[0]
    item.workspace.plugin.processor.running_measurement = meas
    item.workspace.plugin.processor.active = True
    assert not cl_btn.enabled

    item.workspace.plugin.processor.active = False
    assert cl_btn.enabled

    measurements = item.workspace.plugin.enqueued_measurements.measurements
    measurements[0].status = 'COMPLETED'
    measurements[1].status = 'FAILED'

    cl_btn.clicked = True

    def assert_enabled():
        assert not item.workspace.plugin.enqueued_measurements.measurements
        assert not cl_btn.enabled

    exopy_qtbot.wait_until(assert_enabled)


def test_show_monitors(exopy_qtbot, execution_view, dialog_sleep):
    """Test restoring the monitor window.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget

    mon_btn = item.dock_widget().widgets()[5]
    assert not mon_btn.enabled

    with enaml.imports():
        from exopy.measurement.workspace.monitors_window import MonitorsWindow

    meas = item.workspace.plugin.enqueued_measurements.measurements[0]
    mon_win = MonitorsWindow(item, measurement=meas)
    item.workspace.plugin.processor.monitors_window = mon_win

    assert not mon_win.visible

    mon_btn.clicked = True

    def assert_visible():
        assert mon_win.visible

    exopy_qtbot.wait_until(assert_visible)


def test_engine_status(exopy_qtbot, execution_view, dialog_sleep):
    """Test the display of the engine status.

    """
    execution_view.show()
    wait_for_window_displayed(exopy_qtbot, execution_view)
    exopy_qtbot.wait(dialog_sleep)

    item = execution_view.widget
    del item.workspace.plugin.processor.engine

    en_stat = item.dock_widget().widgets()[-1]
    assert not en_stat.visible

    pl = item.workspace.plugin
    pl.processor.engine = pl.create('engine', 'dummy')
    pl.processor.engine.status = 'Stopped'

    def assert_visible():
        assert en_stat.visible
    exopy_qtbot.wait_until(assert_visible)

    assert en_stat.widgets()[1].text == 'Stopped'

    meas = item.workspace.plugin.enqueued_measurements.measurements[0]
    item.workspace.plugin.processor.running_measurement = meas
    item.workspace.plugin.processor.active = True

    assert not en_stat.widgets()[2].enabled
    assert en_stat.widgets()[2].text == 'Shut down'
