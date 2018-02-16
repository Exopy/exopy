# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the MonitoredEntry class.

"""
from exopy.measurement.monitors.text_monitor.entry import MonitoredEntry


def test_entry_formatting(exopy_qtbot):
    """Test that we can correctly format an entry.

    """
    e = MonitoredEntry(name='test', formatting='{a} = {b}',
                       depend_on=['a', 'b'])

    e.update(dict(a=1, b=2, c=3))

    def assert_value():
        assert e.value == '1 = 2'
    exopy_qtbot.wait_until(assert_value)
