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
import enaml

from exopy.testing.util import wait_for_window_displayed, handle_dialog

with enaml.imports():
    from exopy.testing.windows import DockItemTestingWindow
    from exopy.measurement.workspace.tools_edition import (ToolSelector,
                                                           ToolsEditorDockItem)


def test_tool_selector(exopy_qtbot, measurement, dialog_sleep):
    """Selecting a new tool to add to a measurement using the dedicated dialog.

    """
    dial = ToolSelector(measurement=measurement, kind='pre-hook')
    dial.show()
    wait_for_window_displayed(exopy_qtbot, dial)
    widgets = dial.central_widget().widgets()

    assert len(widgets[0].items) == (len(dial.measurement.plugin.pre_hooks) -
                                     len(dial.measurement.pre_hooks))
    widgets[0].selected_item = 'Dummy'

    def assert_selected():
        assert dial.selected_decl
        assert widgets[-2].enabled
        assert widgets[1].text
    exopy_qtbot.wait_until(assert_selected)
    exopy_qtbot.wait(dialog_sleep)

    widgets[-1].clicked = True
    exopy_qtbot.wait(dialog_sleep)


def test_navigation_in_tools_editor(measurement, exopy_qtbot, dialog_sleep):
    """Test navigating among the different measurement tools and accessing
    their editors.

    """
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    wait_for_window_displayed(exopy_qtbot, window)
    exopy_qtbot.wait(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    pages = nb.pages()

    nb.selected_tab = pages[1].name
    exopy_qtbot.wait(10 + dialog_sleep)

    nb.selected_tab = pages[2].name
    exopy_qtbot.wait(10 + dialog_sleep)

    nb.selected_tab = pages[0].name
    exopy_qtbot.wait(10 + dialog_sleep)


def test_manipulating_tools(measurement, exopy_qtbot, dialog_sleep):
    """Test adding/moving/removing tools.

    """
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    wait_for_window_displayed(exopy_qtbot, window)
    exopy_qtbot.wait(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    pre_hook_ed = nb.pages()[0].page_widget()

    # Add a tool
    def add_tool_1(bot, dial):
        widgets = dial.central_widget().widgets()
        widgets[0].selected_item = 'Dummy'
        exopy_qtbot.wait(10 + dialog_sleep)

    with handle_dialog(exopy_qtbot, 'accept', handler=add_tool_1):
        pre_hook_ed.widgets()[-4].clicked = True

    assert 'dummy' in measurement.pre_hooks
    pre_hook_len = len(measurement.pre_hooks)

    # Start to add a tool but cancel.
    with handle_dialog(exopy_qtbot, 'reject'):
        pre_hook_ed.widgets()[-4].clicked = True

    assert len(measurement.pre_hooks) == pre_hook_len

    # Add a tool using wrong id (in principle impossible)
#    def add_tool_2(bot, dial):
#        pl = dial.measurement.plugin
#        dial.selected_decl = pl.get_declarations('pre-hook',
#                                                 ['dummy2'])['dummy2']
#        dial.selected_decl.id = '__'
#        with enaml.imports():
#            from exopy.app.errors.widgets import ErrorsDialog
#
#        with handle_dialog(bot, cls=ErrorsDialog):
#            dial.accept()
#
#    with handle_dialog(exopy_qtbot, handler=add_tool_2, skip_answer=True):
#        pre_hook_ed.widgets()[-4].clicked = True

    # Move up and then down
    pre_hook_ed.selected_id = 'dummy'
    pre_hook_ed.widgets()[-2].clicked = True

    def assert_moving():
        assert list(measurement.pre_hooks)[-2] == 'dummy'
    exopy_qtbot.wait_until(assert_moving)
    exopy_qtbot.wait(dialog_sleep)

    pre_hook_ed.widgets()[-1].clicked = True

    def assert_moving():
        assert list(measurement.pre_hooks)[-1] == 'dummy'
    exopy_qtbot.wait_until(assert_moving)
    exopy_qtbot.wait(dialog_sleep)

    # Remove dummy
    pre_hook_ed.widgets()[-3].clicked = True

    def assert_removed():
        assert 'dummy' not in measurement.pre_hooks
    exopy_qtbot.wait_until(assert_removed)
    exopy_qtbot.wait(dialog_sleep)


def test_ending_with_no_tools(measurement, exopy_qtbot, dialog_sleep):
    """Test adding/moving/removing tools.

    """
    for m in list(measurement.monitors):
        measurement.remove_tool('monitor', m)
    item = ToolsEditorDockItem(measurement=measurement)
    window = DockItemTestingWindow(widget=item)

    window.show()
    window.maximize()
    wait_for_window_displayed(exopy_qtbot, window)
    exopy_qtbot.wait(dialog_sleep)

    nb = item.dock_widget().widgets()[0]
    mon_ed = nb.pages()[1].page_widget()

    # Add a tool
    def add_tool_1(bot, dial):
        widgets = dial.central_widget().widgets()
        widgets[0].selected_item = 'Dummy'
        bot.wait(10 + dialog_sleep)

    with handle_dialog(exopy_qtbot, 'accept', handler=add_tool_1):
        mon_ed.widgets()[-4].clicked = True

    assert 'dummy' in measurement.monitors

    # Move up and then down
    mon_ed.selected_id = 'dummy'
    assert not mon_ed.widgets()[-2].enabled

    assert not mon_ed.widgets()[-1].enabled

    # Remove dummy
    mon_ed.widgets()[-3].clicked = True

    def assert_removed():
        assert 'dummy' not in measurement.monitors
    exopy_qtbot.wait_until(assert_removed)
