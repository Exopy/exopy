# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the widgets dedicated to edit the tools attached to a measurement.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml

from exopy.testing.util import process_app_events, handle_dialog

with enaml.imports():
    from exopy.testing.windows import DockItemTestingWindow
    from exopy.measurement.workspace.tools_edition import (ToolSelector,
                                                           ToolsEditorDockItem)


def test_tool_selector(windows, measurement, dialog_sleep):
    """Selecting a new tool to add to a measurement using the dedicated dialog.

    """
    dial = ToolSelector(measurement=measurement, kind='pre-hook')
    dial.show()
    process_app_events()
    widgets = dial.central_widget().widgets()

    assert len(widgets[0].items) == (len(dial.measurement.plugin.pre_hooks) -
                                     len(dial.measurement.pre_hooks))
    widgets[0].selected_item = 'Dummy'
    process_app_events()
    sleep(dialog_sleep)
    assert dial.selected_decl
    assert widgets[-2].enabled
    assert widgets[1].text

    widgets[-1].clicked = True
    process_app_events()


def test_navigation_in_tools_editor(measurement, windows, dialog_sleep):
    """Test navigating among the different measurement tools and accessing their
    editors.

    """
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    process_app_events()
    sleep(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    pages = nb.pages()

    nb.selected_tab = pages[1].name
    process_app_events()
    sleep(dialog_sleep)

    nb.selected_tab = pages[2].name
    process_app_events()
    sleep(dialog_sleep)

    nb.selected_tab = pages[0].name
    process_app_events()
    sleep(dialog_sleep)


def test_manipulating_tools(measurement, windows, dialog_sleep):
    """Test adding/moving/removing tools.

    """
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    process_app_events()
    sleep(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    pre_hook_ed = nb.pages()[0].page_widget().widgets()[0]

    # Add a tool
    def add_tool_1(dial):
        widgets = dial.central_widget().widgets()
        widgets[0].selected_item = 'Dummy'
        process_app_events()
        sleep(dialog_sleep)

    with handle_dialog('accept', custom=add_tool_1):
        pre_hook_ed.widgets()[-4].clicked = True

    assert 'dummy' in measurement.pre_hooks
    pre_hook_len = len(measurement.pre_hooks)

    # Start to add a tool but cancel.
    with handle_dialog('reject'):
        pre_hook_ed.widgets()[-4].clicked = True

    assert len(measurement.pre_hooks) == pre_hook_len

    # Add a tool using wrong id (in principle impossible)
    # TODO : fix this test second dialog never closes
#    def add_tool_2(dial):
#        pl = dial.measurement.plugin
#        dial.selected_decl = pl.get_declarations('pre-hook',
#                                                 ['dummy2'])['dummy2']
#        dial.selected_decl.id = '__'
#
#    with enaml.imports():
#        from exopy.app.errors.widgets import ErrorsDialog
#
#    with handle_dialog(cls=ErrorsDialog):
#        with handle_dialog(custom=add_tool_2):
#            pre_hook_ed.widgets()[-4].clicked = True

    # Move up and then down
    pre_hook_ed.selected_id = 'dummy'
    pre_hook_ed.widgets()[-2].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert list(measurement.pre_hooks)[-2] == 'dummy'

    pre_hook_ed.widgets()[-1].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert list(measurement.pre_hooks)[-1] == 'dummy'

    # Remove dummy
    pre_hook_ed.widgets()[-3].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert 'dummy' not in measurement.pre_hooks


def test_ending_with_no_tools(measurement, windows, dialog_sleep):
    """Test adding/moving/removing tools.

    """
    for m in list(measurement.monitors):
        measurement.remove_tool('monitor', m)
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    process_app_events()
    sleep(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    mon_ed = nb.pages()[1].page_widget().widgets()[0]

    # Add a tool
    def add_tool_1(dial):
        widgets = dial.central_widget().widgets()
        widgets[0].selected_item = 'Dummy'
        process_app_events()
        sleep(dialog_sleep)

    with handle_dialog('accept', custom=add_tool_1):
        mon_ed.widgets()[-4].clicked = True

    assert 'dummy' in measurement.monitors

    # Move up and then down
    mon_ed.selected_id = 'dummy'
    assert not mon_ed.widgets()[-2].enabled

    assert not mon_ed.widgets()[-1].enabled

    # Remove dummy
    mon_ed.widgets()[-3].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert 'dummy' not in measurement.monitors
