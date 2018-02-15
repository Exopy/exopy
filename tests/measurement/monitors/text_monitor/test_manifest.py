# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the declarative function present in the manifest.

"""
import enaml

from exopy.measurement.monitors.text_monitor.monitor import TextMonitor
with enaml.imports():
    from exopy.testing.util import show_and_close_widget
    from exopy.testing.windows import DockItemTestingWindow
    from exopy.measurement.monitors.text_monitor.monitor_views\
        import TextMonitorEdit, TextMonitorItem


pytest_plugins = str('exopy.testing.measurement.'
                     'monitors.text_monitor.fixtures')


def test_text_monitor_declration_functions(text_monitor_workbench, exopy_qtbot):
    """Test that we can create a monitor and its views.

    """
    m_p = text_monitor_workbench.get_plugin('exopy.measurement')
    decl = m_p.get_declarations('monitor',
                                ['exopy.text_monitor'])['exopy.text_monitor']
    mon = decl.new(text_monitor_workbench, False)
    assert isinstance(mon, TextMonitor)
    edit_view = decl.make_view(text_monitor_workbench, mon)
    assert isinstance(edit_view, TextMonitorEdit)
    item = decl.create_item(text_monitor_workbench, None)
    assert isinstance(item, TextMonitorItem)
    show_and_close_widget(exopy_qtbot, DockItemTestingWindow(widget=item))
