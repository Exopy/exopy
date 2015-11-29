# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the widgets dedicated to edit the tools attached to a measure.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import enaml

from ecpy.testing.util import process_app_events, handle_dialog, get_window

with enaml.imports():
    from ecpy.testing.windows import DockItemTestingWindow
    from ecpy.measure.workspace.tools_edition import (ToolSelector,
                                                      ToolsEditorDockItem)


def test_tool_selector(windows, measure, dialog_sleep):
    """Selecting a new tool to add to a measure using the dedicated dialog.

    """
    dial = ToolSelector(measure=measure, kind='pre-hook')
    dial.show()
    process_app_events()
    widgets = dial.central_widget().widgets()

    assert not widgets[-2].enabled
    assert len(widgets[0].items) == (len(dial.measure.plugin.pre_hooks) -
                                     len(dial.measure.pre_hooks))
    widgets[0].selected_item = 'Dummy'
    process_app_events()
    sleep(dialog_sleep)
    assert dial.selected_decl
    assert widgets[-2].enabled
    assert widgets[1].text

    widgets[-1].clicked = True
    process_app_events()


def test_navigation_in_tools_editor(measure, windows, dialog_sleep):
    """Test navigating among the different measure tools and accessing their
    editors.

    """
    item = ToolsEditorDockItem(measure=measure)
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


def test_manipulating_tools(measure, windows, dialog_sleep):
    """Test adding/moving/removing tools.

    """
    item = ToolsEditorDockItem(measure=measure)
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

        widgets[-2].clicked = True

    with handle_dialog(custom=add_tool_1):
        pre_hook_ed.widgets()[-4].clicked = True

    assert 'dummy' in measure.pre_hooks
    pre_hook_len = len(measure.pre_hooks)

    # Start to add a tool but cancel.
    with handle_dialog('reject'):
        pre_hook_ed.widgets()[-4].clicked = True

    assert len(measure.pre_hooks) == pre_hook_len

    # Add a tool using wrong id (in principle impossible)
    # TODO : fix this test second dialog never closes
#    def add_tool_2(dial):
#        pl = dial.measure.plugin
#        dial.selected_decl = pl.get_declarations('pre-hook',
#                                                 ['dummy2'])['dummy2']
#        dial.selected_decl.id = '__'
#
#    with enaml.imports():
#        from ecpy.app.errors.widgets import ErrorsDialog
#
#    with handle_dialog(cls=ErrorsDialog):
#        with handle_dialog(custom=add_tool_2):
#            pre_hook_ed.widgets()[-4].clicked = True

    # Move up and then down
    pre_hook_ed.selected_id = 'Dummy'
    pre_hook_ed.widgets()[-2].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert measure.pre_hooks.keys()[-2] == 'dummy'

    pre_hook_ed.widgets()[-1].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert measure.pre_hooks.keys()[-1] == 'dummy'

    # Remove dummy
    pre_hook_ed.widgets()[-3].clicked = True
    process_app_events()
    sleep(dialog_sleep)
    assert 'dummy' not in measure.pre_hooks
