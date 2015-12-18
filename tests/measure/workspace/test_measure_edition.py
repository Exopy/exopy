# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets related to measure edition tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep
from collections import namedtuple

import pytest
import enaml
from atom.api import Value

from ecpy.testing.measure.fixtures import measure as m_build
from ecpy.testing.util import process_app_events, handle_dialog, CallSpy
from ecpy.tasks.tasks.logic.loop_exceptions_tasks import BreakTask

with enaml.imports():
    from ecpy.testing.windows import DockItemTestingWindow
    from ecpy.measure.workspace.measure_edition import (MeasureEditorDockItem,
                                                        MeasureEditorDialog,
                                                        SaveAction, build_task)


pytest_plugins = str('ecpy.testing.measure.workspace.fixtures'),


@pytest.fixture
def edition_view(measure, workspace, windows):
    """Start plugins and add measures before creating the execution view.

    """
    pl = measure.plugin
    pl.edited_measures.add(measure)
    measure.root_task.add_child_task(0, BreakTask(name='Test'))

    item = MeasureEditorDockItem(workspace=workspace,
                                 measure=measure,
                                 name='test')
    return DockItemTestingWindow(widget=item)


def test_save_action(workspace, measure, windows):
    """Test that save action calls the proper commands.

    """
    act = SaveAction(workspace=workspace,
                     action_context={'data': (None, None,
                                              measure.root_task, None)})

    with handle_dialog('reject'):
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
            process_app_events()
        assert ex.value.cmd == 'ecpy.app.errors.signal'
    finally:
        CorePlugin.invoke_command = old


def test_build_task(workspace, windows):
    """Test getting the dialog to create a new task.

    """
    with handle_dialog('reject'):
        build_task(workspace.workbench)


def test_sync_name(edition_view, dialog_sleep):
    """Test the synchronisation between the measure name and widget.

    """
    edition_view.show()
    process_app_events()
    sleep(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    meas = ed.measure
    field = ed.widgets()[1]

    meas.name = '__dummy'
    process_app_events()
    assert meas.name == field.text

    field.text = 'dummy__'
    process_app_events()
    assert meas.name == field.text


def test_sync_id(edition_view, dialog_sleep):
    """Test the synchronisation between the measure id and widget.

    """
    edition_view.show()
    process_app_events()
    sleep(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    meas = ed.measure
    field = ed.widgets()[3]

    meas.id = '101'
    process_app_events()
    assert meas.id == field.text

    field.text = '202'
    process_app_events()
    assert meas.id == field.text


def test_switching_between_tasks(edition_view, dialog_sleep):
    """Test switching between tasks which lead to different selected editors.

    """
    edition_view.show()
    edition_view.maximize()
    process_app_events()
    sleep(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]

    nb = ed.widgets()[-1]
    nb.selected_tab = 'ecpy.database_access'
    process_app_events()
    sleep(dialog_sleep)

    tree = ed.widgets()[5]
    tree.selected_item = ed.measure.root_task.children[0]
    process_app_events()
    sleep(dialog_sleep)

    assert nb.selected_tab == 'ecpy.standard'

    tree.selected_item = ed.measure.root_task
    process_app_events()
    sleep(dialog_sleep)


def test_switching_the_linked_measure(edition_view, dialog_sleep):
    """Test changing the measure edited by the editor.

    """
    edition_view.show()
    process_app_events()
    sleep(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]

    ed.measure = m_build(ed.workspace.workbench)

    process_app_events()
    sleep(dialog_sleep)

    tree = ed.widgets()[5]
    assert tree.selected_item == ed.measure.root_task


def test_creating_tools_edition_panel(edition_view, dialog_sleep):
    """Test creating the tool edition panel using the button.

    """
    edition_view.show()
    process_app_events()
    sleep(dialog_sleep)

    ed = edition_view.widget.dock_widget().widgets()[0]
    btn = ed.widgets()[4]

    btn.clicked = True
    process_app_events()

    assert len(edition_view.area.dock_items()) == 2


def test_closing_measure(edition_view, monkeypatch, dialog_sleep):
    """Test closing the measure dock item.

    """
    edition_view.show()
    process_app_events()
    sleep(dialog_sleep)

    # Open the tools edition panel to check that we will properly close the
    # it later
    ed = edition_view.widget.dock_widget().widgets()[0]
    btn = ed.widgets()[4]

    btn.clicked = True
    process_app_events()

    # Monkeypatch question (handle_dialog does not work on it on windows)
    with enaml.imports():
        from ecpy.measure.workspace import measure_edition

    monkeypatch.setattr(measure_edition, 'question', lambda *args: None)
    edition_view.widget.proxy.on_closed()
    edition_view.widget.measure.name = 'First'
    process_app_events()
    assert len(edition_view.area.dock_items()) == 2
    sleep(dialog_sleep)

    false_btn = namedtuple('FalseBtn', ['action'])
    monkeypatch.setattr(measure_edition, 'question',
                        lambda *args: false_btn('reject'))
    edition_view.widget.proxy.on_closed()
    edition_view.widget.measure.name = 'Second'
    process_app_events()
    assert len(edition_view.area.dock_items()) == 2
    sleep(dialog_sleep)

    monkeypatch.setattr(measure_edition, 'question',
                        lambda *args: false_btn('accept'))
    edition_view.widget.proxy.on_closed()
    process_app_events()
    assert len(edition_view.area.dock_items()) == 0


def test_measure_edition_dialog(workspace, measure, windows, monkeypatch,
                                dialog_sleep):
    """Test creating a measure edition dialog.

    """
    dialog = MeasureEditorDialog(workspace=workspace, measure=measure)
    dialog.show()
    process_app_events()
    sleep(dialog_sleep)

    from ecpy.measure.workspace.workspace import MeasureSpace

    def false_save(self, meas, *args, **kwargs):
        false_save.called = 1

    monkeypatch.setattr(MeasureSpace, 'save_measure', false_save)

    btn = dialog.central_widget().widgets()[-1]
    btn.clicked = True
    process_app_events()
    assert false_save.called

    dialog.close()
