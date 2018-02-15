# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets related to measurement edition tasks.

"""
from collections import namedtuple

import pytest
import enaml

from exopy.testing.measurement.fixtures import measure as m_build
from exopy.testing.util import (handle_dialog, wait_for_window_displayed,
                               wait_for_destruction)
from exopy.tasks.tasks.logic.loop_exceptions_tasks import BreakTask
from exopy.utils.widgets.qt_clipboard import CLIPBOARD

with enaml.imports():
    from exopy.testing.windows import DockItemTestingWindow
    from exopy.measurement.workspace.measurement_edition\
        import (MeasurementEditorDockItem,
                MeasureEditorDialog,
                SaveAction, build_task,
                TaskCopyAction)


pytest_plugins = str('exopy.testing.measurement.workspace.fixtures'),


@pytest.fixture
def edition_view(measurement, workspace, exopy_qtbot):
    """Start plugins and add measurements before creating the execution view.

    """
    pl = measurement.plugin
    pl.edited_measurements.add(measurement)
    measurement.root_task.add_child_task(0, BreakTask(name='Test'))

    item = MeasurementEditorDockItem(workspace=workspace,
                                     measurement=measurement,
                                     name='test')
    return DockItemTestingWindow(widget=item)


def test_copy_action(workspace, measurement, exopy_qtbot):
    """Test copying a task does work.

    """
    task = BreakTask(name='Test')
    measurement.root_task.add_child_task(0, task)
    action = TaskCopyAction(workspace=workspace,
                            action_context=dict(copyable=True,
                                                data=(None, None, task, None)))
    action.triggered = True
    new = CLIPBOARD.instance
    assert isinstance(new, BreakTask)
    assert new.name == 'Test'


def test_save_action(exopy_qtbot, workspace, measure):
    """Test that save action calls the proper commands.

    """
    act = SaveAction(workspace=workspace,
                     action_context={'data': (None, None,
                                              measurement.root_task, None)})

    with handle_dialog(exopy_qtbot, 'reject'):
        act.triggered = True

    class CmdException(Exception):

        def __init__(self, cmd, opts):
            self.cmd = cmd

    def invoke(self, cmd, opts, caller=None):
        raise CmdException(cmd, opts)

    from enaml.workbench.core.core_plugin import CorePlugin
    old = CorePlugin.invoke_command
    CorePlugin.invoke_command = invoke

    try:
        with pytest.raises(CmdException) as ex:
            act.triggered = True
            exopy_qtbot.wait(10)
        assert ex.value.cmd == 'exopy.app.errors.signal'
    finally:
        CorePlugin.invoke_command = old


def test_build_task(workspace, exopy_qtbot):
    """Test getting the dialog to create a new task.

    """
    with handle_dialog(exopy_qtbot, 'reject'):
        build_task(workspace.workbench)


def test_sync_name(exopy_qtbot, edition_view, dialog_sleep):
    """Test the synchronisation between the measure name and widget.

    """
    edition_view.show()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    meas = ed.measurement
    field = ed.widgets()[1]

    def assert_field_text():
        assert meas.name == field.text

    meas.name = '__dummy'
    exopy_qtbot.wait_until(assert_field_text)

    field.text = 'dummy__'
    exopy_qtbot.wait_until(assert_field_text)


def test_sync_id(exopy_qtbot, edition_view, dialog_sleep):
    """Test the synchronisation between the measure id and widget.

    """
    edition_view.show()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    meas = ed.measurement
    field = ed.widgets()[3]

    def assert_field_text():
        assert meas.id == field.text

    meas.id = '101'
    exopy_qtbot.wait_until(assert_field_text)

    field.text = '202'
    exopy_qtbot.wait_until(assert_field_text)


def test_switching_between_tasks(exopy_qtbot, edition_view, dialog_sleep):
    """Test switching between tasks which lead to different selected editors.

    """
    edition_view.show()
    edition_view.maximize()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]

    nb = ed.widgets()[-1]
    nb.selected_tab = 'exopy.database_access'
    exopy_qtbot.wait(10 + dialog_sleep)

    tree = ed.widgets()[5]
    tree.selected_item = ed.measurement.root_task.children[0]

    def assert_tab():
        assert nb.selected_tab == 'exopy.standard'
    exopy_qtbot.wait_until(assert_tab)

    tree.selected_item = ed.measurement.root_task
    exopy_qtbot.wait(10 + dialog_sleep)


def test_switching_the_linked_measure(exopy_qtbot, edition_view, dialog_sleep):
    """Test changing the measure edited by the editor.

    """
    edition_view.show()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]

    ed.measurement = m_build(ed.workspace.workbench)

    def assert_selected():
        tree = ed.widgets()[5]
        assert tree.selected_item == ed.measurement.root_task
    exopy_qtbot.wait_until(assert_selected)


def test_creating_tools_edition_panel(exopy_qtbot, edition_view, dialog_sleep):
    """Test creating the tool edition panel using the button.

    """
    edition_view.show()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    btn = ed.widgets()[4]

    btn.clicked = True

    def assert_created():
        assert len(edition_view.area.dock_items()) == 2
    exopy_qtbot.wait_until(assert_created)


def test_closing_measure(exopy_qtbot, edition_view, monkeypatch, dialog_sleep):
    """Test closing the measure dock item.

    """
    edition_view.show()
    wait_for_window_displayed(exopy_qtbot, edition_view)
    exopy_qtbot.wait(dialog_sleep)

    # Open the tools edition panel to check that we will properly close the
    # it later
    ed = edition_view.widget.dock_widget().widgets()[0]
    btn = ed.widgets()[4]

    btn.clicked = True
    exopy_qtbot.wait(10)

    # Monkeypatch question (handle_dialog does not work on it on Windows)
    with enaml.imports():
        from exopy.measurement.workspace import measurement_edition

    monkeypatch.setattr(measurement_edition, 'question', lambda *args: None)
    edition_view.widget.proxy.on_closed()
    edition_view.widget.measurement.name = 'First'

    def assert_dock():
        assert len(edition_view.area.dock_items()) == 2
    exopy_qtbot.wait_until(assert_dock)
    exopy_qtbot.wait(dialog_sleep)

    false_btn = namedtuple('FalseBtn', ['action'])
    monkeypatch.setattr(measurement_edition, 'question',
                        lambda *args: false_btn('reject'))
    edition_view.widget.proxy.on_closed()
    edition_view.widget.measurement.name = 'Second'

    exopy_qtbot.wait_until(assert_dock)
    exopy_qtbot.wait(dialog_sleep)

    monkeypatch.setattr(measurement_edition, 'question',
                        lambda *args: false_btn('accept'))
    edition_view.widget.proxy.on_closed()

    def assert_dock_zero():
        assert len(edition_view.area.dock_items()) == 0
    exopy_qtbot.wait_until(assert_dock_zero)


def test_measurement_edition_dialog(exopy_qtbot, workspace, measurement, monkeypatch,
                                dialog_sleep):
    """Test creating a measure edition dialog.

    """
    dialog = MeasureEditorDialog(workspace=workspace, measurement=measurement)
    dialog.show()
    wait_for_window_displayed(exopy_qtbot, dialog)
    exopy_qtbot.wait(dialog_sleep)

    from exopy.measurement.workspace.workspace import MeasurementSpace

    def false_save(self, meas, *args, **kwargs):
        false_save.called = 1

    monkeypatch.setattr(MeasurementSpace, 'save_measurement', false_save)

    btn = dialog.central_widget().widgets()[-1]
    btn.clicked = True

    def assert_called():
        assert false_save.called
    exopy_qtbot.wait_until(assert_called)

    dialog.close()
    wait_for_destruction(exopy_qtbot, dialog)
