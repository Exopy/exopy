# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the declarative function present in the manifest.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ecpy.measure.monitors.text_monitor.monitor import TextMonitor
with enaml.imports():
    from ecpy.testing.util import show_and_close_widget
    from ecpy.testing.windows import DockItemTestingWindow
    from ecpy.measure.monitors.text_monitor.monitor_views\
        import TextMonitorEdit, TextMonitorItem


pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures')


def test_text_monitor_declration_functions(text_monitor_workbench):
    """Test that we can create a monitor and its views.

    """
    m_p = text_monitor_workbench.get_plugin('ecpy.measure')
    decl = m_p.get_declarations('monitor',
                                ['ecpy.text_monitor'])['ecpy.text_monitor']
    mon = decl.new(text_monitor_workbench, False)
    assert isinstance(mon, TextMonitor)
    edit_view = decl.make_view(text_monitor_workbench, mon)
    assert isinstance(edit_view, TextMonitorEdit)
    item = decl.create_item(text_monitor_workbench, None)
    assert isinstance(item, TextMonitorItem)
    show_and_close_widget(DockItemTestingWindow(widget=item))
